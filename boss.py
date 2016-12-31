'''
boss.py

boss is zeromq based, multi-threading Task distributing framework

Interfaces:
    start(action, num_workers=3)
    assign_task(task):
    stop()
    have_all_tasks_done():
    tasks():


Classes:
    Task
'''
import time
import zmq
import uuid
import threading
import logging
import signal


logger = logging.getLogger('boss.streambot')
signal.signal(signal.SIGINT, signal.SIG_DFL)
_CONTEXT = zmq.Context()


_GLOBAL_TASK_LOCK = threading.Lock()
_WORKER_TASK = 'WORKER_TASK'
_WORKER_RESULT = 'WORKER_RESULT'
_WORKER_ACK = 'WORKER_ACK'

_WORKING_THREADS = []   # list of working threads

_TASK_OUT_SOCKET = None  # PUSH socket for dispatching _TASKS to workers
_TASKS = {}  # All tasks, key: Task.id, value: Task object


class Task(object):
    def __init__(self, task_id, command, status='START'):
        '''
        @param task_id Unique id for a task
        @param command An object

        'STOP' status reserved for stopping working thread
        '''
        self.id = task_id
        self.command = command
        self.status = status

    def set_done(self):
        self.status = 'DONE'

    def is_done(self):
        return 'DONE' == self.status

    def set_failed(self):
        self.status = 'FAILED'

    def is_failed(self):
        return 'FAILED' == self.status

    def __repr__(self):
        return 'task {id}: stauts {status}'.format(id=self.id, status=self.status)


class _WorkerThread(threading.Thread):
    '''
    boss's worker thread

    read Task from task_in socket, which binds to inproc://WORKER_TASK
    send Task result to result_out socket, which binds to inproc://WORKER_RESULT
    also sync to client via worker_ack_out socket, wich binds to inproc://WORKER_ACK
    also command socket, which binds to inproc://{id}

    action is the Task handler: bool(Task). This is a blocking call.
    '''
    def __init__(self, action):
        '''
        @param action A function implements "bool (Task)"
        '''
        threading.Thread.__init__(self)
        self.id = uuid.uuid4()
        self.task_in = _CONTEXT.socket(zmq.PULL)
        self.result_out = _CONTEXT.socket(zmq.REQ)
        self.worker_ack_out = _CONTEXT.socket(zmq.REQ)
        self.command_in = _CONTEXT.socket(zmq.PULL)
        self.command_out = _CONTEXT.socket(zmq.PUSH)
        self.command_in.connect('inproc://{id}'.format(id=self.id))
        self.command_out.bind('inproc://{id}'.format(id=self.id))
        self.poller = zmq.Poller()
        self.poller.register(self.command_in, zmq.POLLIN)
        self.poller.register(self.task_in, zmq.POLLIN)

        self.action = action
        logger.debug('create worker [{id}]'.format(id=self.id))

    def run(self):
        try:
            # init sockets
            self.task_in.connect('inproc://{proc_name}'.format(proc_name=_WORKER_TASK))
            self.result_out.connect('inproc://{proc_name}'.format(proc_name=_WORKER_RESULT))

            # sync worker to boss
            self.worker_ack_out.connect('inproc://{proc_name}'.format(proc_name=_WORKER_ACK))
            self.worker_ack_out.send(b'')
            logger.debug('waiting to start worker [{id}]'.format(id=self.id))
            self.worker_ack_out.recv()  # blocking wait client to response, then start working process
            logger.debug('worker [{id}] stats'.format(id=self.id))

            # main working loop
            while True:
                logger.debug('worker [{id}] is waiting for task'.format(id=self.id))
                socks = dict(self.poller.poll())
                if self.command_in in socks and socks[self.command_in] == zmq.POLLIN:
                    logger.debug('stop() received')
                    break

                if self.task_in in socks and socks[self.task_in] == zmq.POLLIN:
                    task_msg = self.task_in.recv_json()
                    logger.debug('receive task_msg: {msg}'.format(msg=task_msg))
                    if 'STOP' == task_msg['status']:
                        break

                    task = Task(task_msg['id'], task_msg['command'])
                    logger.debug('worker [{id}] is working on {task}'.format(id=self.id, task=task.id))

                    if self.action(task):
                        logger.debug('worker [{id}]: Task done'.format(id=self.id))
                        task.set_done()
                    else:
                        logger.debug('worker [{id}]: Task failed'.format(id=self.id))
                        task.set_failed()

                    self.result_out.send_json(task.__dict__)

                    logger.debug('worker [{id}] is sending out result'.format(id=self.id))
                    self.result_out.recv()
        except Exception as e:
            logger.error('Error in worker [{id}]'.format(id=self.id))
            logger.exception(e)

    def stop(self):
        '''
        properly stopping a _WorkerThread is:

        worker.stop()
        worker.join()
        '''
        self.command_out.send('STOP')


class _SinkerThread(threading.Thread):
    '''
    Sinker thread

    receive Task result from result_in socket, which binds to inproc://WORKER_RESULT
    update global _TASKS dict
    '''
    def __init__(self):
        threading.Thread.__init__(self)
        self.id = uuid.uuid4()
        self.result_in = _CONTEXT.socket(zmq.REP)
        self.command_in = _CONTEXT.socket(zmq.PULL)
        self.command_out = _CONTEXT.socket(zmq.PUSH)
        self.command_in.connect('inproc://{id}'.format(id=self.id))
        self.command_out.bind('inproc://{id}'.format(id=self.id))
        self.poller = zmq.Poller()
        self.poller.register(self.command_in, zmq.POLLIN)
        self.poller.register(self.result_in, zmq.POLLIN)
        logger.debug('create sinker [{id}]'.format(id=self.id))

    def run(self):
        try:
            global _TASKS
            self.result_in.bind('inproc://{proc_name}'.format(proc_name=_WORKER_RESULT))

            while True:
                socks = dict(self.poller.poll())
                if self.command_in in socks and socks[self.command_in] == zmq.POLLIN:
                    logger.debug('stop() received')
                    break

                if self.result_in in socks and socks[self.result_in] == zmq.POLLIN:
                    task_msg = self.result_in.recv_json()

                    task = Task(task_msg['id'], task_msg['command'], task_msg['status'])
                    logger.debug('sink [{id}] received result of task {task_id}'.format(id=self.id, task_id=task.id))
                    _GLOBAL_TASK_LOCK.acquire()
                    _TASKS[task.id] = task
                    _GLOBAL_TASK_LOCK.release()
                    self.result_in.send(b'')

        except Exception as e:
            logger.error('Error in sink [{id}]'.format(id=self.id))
            logger.exception(e)

    def stop(self):
        self.command_out.send('STOP')


def _sync_workers(ack_in, num_workers):
    '''
    synchronise active workers
    @param ack_in worker thread ack in socket, binds to inproc://_WORKER_ACK
    @param num_workers Number of workers
    '''
    num_active_workers = 0
    while num_active_workers < num_workers:
        logger.debug('sync with worker {n}'.format(n=num_active_workers))
        ack_in.recv()
        ack_in.send(b'')
        num_active_workers += 1


def start(action, num_workers=3):
    '''
    @param action bool(Task)
    @num_workers Number workers, default 3
    '''
    global _WORKING_THREADS
    _WORKING_THREADS = []

    global _TASKS
    _TASKS = {}

    global _TASK_OUT_SOCKET
    _TASK_OUT_SOCKET = None

    # bind worker ack
    ack_in = _CONTEXT.socket(zmq.REP)
    ack_in.bind('inproc://{proc_name}'.format(proc_name=_WORKER_ACK))

    # create sink
    sinker_thread = _SinkerThread()
    _WORKING_THREADS.append(sinker_thread)
    sinker_thread.start()

    # create workers
    logger.debug('create workers')
    for i in range(num_workers):
        worker_thread = _WorkerThread(action=action)
        _WORKING_THREADS.append(worker_thread)
        worker_thread.start()

    try:
        logger.debug('sync workers')
        _sync_workers(ack_in, num_workers)

        # create _TASK_OUT_SOCKET
        _TASK_OUT_SOCKET = _CONTEXT.socket(zmq.PUSH)
        _TASK_OUT_SOCKET.bind('inproc://{proc_name}'.format(proc_name=_WORKER_TASK))
    except Exception as e:
        logger.error('Error in start worker')
        logger.exception(e)
        stop()


def stop():
    '''
    stop all working threads, including workers and sinker
    '''
    for t in _WORKING_THREADS:
        logger.debug('Stopping thread {id}'.format(id=t.id))
        t.stop()
        t.join()


def assign_task(task):
    '''
    Assign task to the active worker
    @param task Task object
    '''
    global _TASK_OUT_SOCKET
    global _TASKS
    if not _TASK_OUT_SOCKET:
        logger.error('Error _TASK_OUT_SOCKET is None. start() the boss')
        return

    _GLOBAL_TASK_LOCK.acquire()
    if task.id in _TASKS:
        logger.debug('task: {task_id} is processed'.format(task_id=task.id))
        _GLOBAL_TASK_LOCK.release()
    else:
        _TASKS[task.id] = task
        _GLOBAL_TASK_LOCK.release()
        logger.debug('send task: {task}'.format(task=task.id))
        _TASK_OUT_SOCKET.send_json(task.__dict__)


def have_all_tasks_done():
    '''
    Check whether all tasks done
    @return True if all tasks done
    '''
    _GLOBAL_TASK_LOCK.acquire()
    all_TASKS_done = True
    for k, v in _TASKS.items():
        if not v.is_done() and not v.is_failed():
            all_TASKS_done = False
            break
    _GLOBAL_TASK_LOCK.release()
    return all_TASKS_done


def tasks():
    '''
    @return array of assigned Task instances
    '''
    return _TASKS


def _example():
    # setup logger
    logging.basicConfig(level=logging.DEBUG)

    def simple_action(task):
        '''
        @param task Task instance
        @return True indicating task done, False otherwise
        '''
        logger.debug('procesing task: {id}'.format(id=task.id))
        import random
        time.sleep(random.randint(1, 10))
        return True

    # start boss (including worker and sinker processes)
    start(num_workers=2, action=simple_action)

    # dispatch dummy tasks
    for i in range(5):
        import random
        task_id = random.randint(1, 30)
        task = Task(task_id, {})
        assign_task(task)
        time.sleep(0.5)

    # check all tasks done before stop boss
    total_check = 0
    while not have_all_tasks_done():
        logger.debug('Waiting for all _TASKS done')
        time.sleep(1)
        total_check += 1
        if total_check > 50:
            break

    # stop boss (including worker and sinker processes)
    stop()

    all_tasks = tasks()
    logger.debug(all_tasks)


if __name__ == '__main__':
    _example()
