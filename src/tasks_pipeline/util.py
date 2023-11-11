def flatten_tasks(task):
    tasks = []
    tasks.append(task)
    for child in task.subtasks:
        tasks.extend(flatten_tasks(child))
    return tasks


def tasks_apply(task, f):
    f(task)
    for child in task.subtasks:
        tasks_apply(child, f)
