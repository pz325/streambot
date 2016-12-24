import unittest
import boss


class TaskTest(unittest.TestCase):
    def test_constructor_default_status(self):
        task = boss.Task(1, {})
        self.assertEqual(task.status, 'START')

    def test_constructor_id(self):
        task_id = 1
        task = boss.Task(task_id, {})
        self.assertEqual(task.id, task_id)

    def test_constructor_command(self):
        command = {'cmd', 'cmd'}
        task = boss.Task(1, command)
        self.assertIn('cmd', task.command)

    def test_set_done(self):
        task = boss.Task(1, {})
        task.set_done()
        self.assertEqual(task.status, 'DONE')

    def test_is_done(self):
        task = boss.Task(1, {}, 'DONE')
        self.assertTrue(task.is_done())

    def test_set_failed(self):
        task = boss.Task(1, {})
        task.set_failed()
        self.assertEqual(task.status, 'FAILED')

    def teste_is_failed(self):
        task = boss.Task(1, {}, 'FAILED')
        self.assertTrue(task.is_failed())
