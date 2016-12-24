import unittest
import boss
import time


def done_action(task):
    return True


def failed_action(task):
    return False


def half_done_half_failed_action(task):
    return 0 == task.id % 2


class TaskBoss(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_duplicated_tasks_run_only_once(self):
        boss.start(action=half_done_half_failed_action)
        num_unique_tasks = 10
        for i in range(num_unique_tasks):
            task = boss.Task(i, {})
            # assign each task twice
            boss.assign_task(task)
            boss.assign_task(task)

        total_check = 0
        while not boss.have_all_tasks_done():
            boss._print('Waiting for all _TASKS done')
            time.sleep(1)
            total_check += 1
            if total_check > 10:
                self.fail('workers have not stpped in time')

        boss.stop()
        self.assertEqual(len(boss.tasks()), num_unique_tasks)

    def test_boss_can_shut_down(self):
        boss.start(action=half_done_half_failed_action)
        for i in range(10):
            task = boss.Task(i, {})
            boss.assign_task(task)

        total_check = 0
        while not boss.have_all_tasks_done():
            boss._print('Waiting for all _TASKS done')
            time.sleep(1)
            total_check += 1
            if total_check > 10:
                self.fail('workers have not stpped in time')

        boss.stop()
        for t in boss._WORKING_THREADS:
            self.assertFalse(t.isAlive())

    def test_done_and_failed_tasks_saved(self):
        boss.start(action=half_done_half_failed_action)
        for i in range(10):
            task = boss.Task(i, {})
            boss.assign_task(task)

        total_check = 0
        while not boss.have_all_tasks_done():
            boss._print('Waiting for all _TASKS failed')
            time.sleep(1)
            total_check += 1
            if total_check > 10:
                self.fail('workers have not stpped in time')

        boss.stop()
        print(boss.tasks())
        for k, v in boss.tasks().items():
            if 0 == k % 2:
                self.assertTrue(v.is_done())
            else:
                self.assertTrue(v.is_failed())

    def test_done_tasks_saved(self):
        boss.start(action=done_action)
        for i in range(10):
            task = boss.Task(i, {})
            boss.assign_task(task)

        total_check = 0
        while not boss.have_all_tasks_done():
            boss._print('Waiting for all _TASKS failed')
            time.sleep(1)
            total_check += 1
            if total_check > 10:
                self.fail('workers have not stpped in time')

        boss.stop()
        print(boss.tasks())
        for k, v in boss.tasks().items():
            self.assertTrue(v.is_done())

    def test_failed_tasks_saved(self):
        boss.start(action=failed_action)
        for i in range(10):
            task = boss.Task(i, {})
            boss.assign_task(task)

        total_check = 0
        while not boss.have_all_tasks_done():
            boss._print('Waiting for all _TASKS failed')
            time.sleep(1)
            total_check += 1
            if total_check > 10:
                self.fail('workers have not stpped in time')

        boss.stop()
        for k, v in boss.tasks().items():
            self.assertTrue(v.is_failed())
