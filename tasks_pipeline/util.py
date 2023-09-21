
def flatten_tasks(task):
    tasks = []
    tasks.append(task)
    for child in task.get('tasks', []):
        tasks.extend(flatten_tasks(child))
    return tasks


def tasks_apply(task, f):
    f(task)
    for child in task.get('tasks', []):
        tasks_apply(child, f)
