#!/usr/bin/env python
import string
import inspect


class ActStatus(object):
    """ An enumerator representing the status of an act """
    SUCCESS = 0
    FAIL = 1
    RUN = 2


class Act(object):
    """ An act is a node in a behavior tree that uses coroutines in its tick function """

    def __init__(self, children = [], name = "", *args, **kwargs):
        self.name = name
        self.iterator = self.tick()
        if children is None:
            children = []

        self.children = children

    def tick(self):
        pass

    def reset(self):
        self.iterator = self.tick()
        for child in self.children:
            child.reset()

    def add_child(self, child):
        self.children.append(child)

    def remove_child(self, child):
        self.children.remove(child)

    def suspend(self):
        pass

    def resume(self):
        pass

    def __enter__(self):
        return self.name;

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            return False
        return True


class Select(Act):
    """
    Runs all of its child acts in sequence until one succeeds.
    """

    def __init__(self, children = [], name = "Select", *args, **kwargs):
        super(Select, self).__init__(children, name, *args, **kwargs)
        self.current_child = None

    def tick(self):
        for child in self.children:
            self.current_child = child
            for status in child.iterator:
                if status == ActStatus.RUN:
                    yield status
                elif status == ActStatus.FAIL:
                    yield ActStatus.RUN
                else:
                    yield status
                    return
        yield ActStatus.FAIL

    def suspend(self):
        if self.current_child:
            self.current_child.suspend()

    def resume(self):
        if self.current_child:
            self.current_child.resume()

    def reset(self):
        self.current_child = None
        Act.reset(self)


class Sequence(Act):
    """
    Runs all of its children in sequence until all succeed
    """

    def __init__(self, children = [], name = "Sequence", *args, **kwargs):
        super(Sequence, self).__init__(children, name, *args, **kwargs)
        self.current_child = None

    def tick(self):
        for child in self.children:
            current_child = child
            for status in child.iterator:
                if status == ActStatus.RUN:
                    yield status
                elif status == ActStatus.FAIL:
                    yield ActStatus.FAIL
                    return
                else:
                    yield ActStatus.RUN

        yield ActStatus.SUCCESS

    def suspend(self):
        if self.current_child:
            self.current_child.suspend()

    def resume(self):
        if self.current_child:
            self.current_child.resume()

    def reset(self):
        self.current_child = None
        Act.reset(self)

class Parallel(Act):
    """
    Runs all of its children in parallel until one succeeds
    """

    def __init__(self, children = [], name = "Parallel", *args, **kwargs):
        super(Parallel, self).__init__(children, name, *args, **kwargs)

    def tick(self):
        num_fails = 0
        while True:
            if num_fails >= len(self.children):
                yield ActStatus.FAIL
                return
            try:
                for child in self.children:
                    status = child.iterator.next()

                    if status == ActStatus.SUCCESS:
                        yield ActStatus.SUCCESS
                        return
                    elif status == ActStatus.FAIL:
                        num_fails += 1

            except StopIteration:
                continue

    def suspend(self):
        for child in self.children:
            child.suspend()

    def resume(self):
        for child in self.children:
            child.resume()

class Loop(Act):
    """
    Runs all of its children for some number of iters, regardless of whether one succeeds. If iterations is set to
    -1, loops indefinitely. If any child fails, returns FAIL.
    """

    def __init__(self, children = [], name = "Loop", num_iter = -1, *args, **kwargs):
        super(Loop, self).__init__(children, name, *args, **kwargs)
        self.num_iter = num_iter
        self.iter = 1
        self.current_child = None

    def tick(self):
        while True:
            if self.num_iter != -1 and self.iter >= self.num_iter:
                yield ActStatus.SUCCESS
                return

            for child in self.children:
                current_child = child
                for status in child.iterator:
                    if status == ActStatus.RUN:
                        yield status
                    elif status == ActStatus.SUCCESS:
                        yield ActStatus.RUN
                    elif status == ActStatus.FAIL:
                        yield ActStatus.FAIL
                        return
                child.reset()
            self.iter += 1
        yield ActStatus.SUCCESS

    def suspend(self):
        if self.current_child:
            self.current_child.suspend()

    def resume(self):
        if self.current_child:
            self.current_child.resume()


class IgnoreFail(Act):
    """
        Always return either RUNNING or SUCCESS.
    """

    def __init__(self, children = [], name = "IgnoreFail", *args, **kwargs):
        super(IgnoreFail, self).__init__(children, name, *args, **kwargs)
        self.current_child = None

    def tick(self):
        for child in self.children:
            for status in child.iterator:
                if status == ActStatus.FAIL:
                    yield ActStatus.SUCCESS
                else:
                    yield status
        yield ActStatus.SUCCESS

    def suspend(self):
        if self.current_child:
            self.current_child.suspend()

    def resume(self):
        if self.current_child:
            self.current_child.resume()


class Not(Act):
    """
        Returns FAIL on SUCCESS, and SUCCESS on FAIL
    """

    def __init__(self, children = [], name = "Not", *args, **kwargs):
        super(Not, self).__init__(children, name, *args, **kwargs)
        self.current_child = None

    def tick(self):
        for child in self.children:
            for status in child.iterator:
                if status == ActStatus.FAIL:
                    yield ActStatus.SUCCESS
                elif status == ActStatus.SUCCESS:
                    yield ActStatus.FAIL
                else:
                    yield status
        yield ActStatus.SUCCESS

    def suspend(self):
        if self.current_child:
            self.current_child.suspend()

    def resume(self):
        if self.current_child:
            self.current_child.resume()


class Wrap(Act):
    """
    Wraps a function that returns FAIL or SUCCESS
    """

    def __init__(self, wrap_function, children = [], name = "", *args, **kwargs):
        super(Wrap, self).__init__(children, name, *args, **kwargs)
        self.fn = wrap_function
        self.name = "Wrap " + inspect.getsource(self.fn)

    def tick(self):
        yield self.fn()


def print_act_tree(printTree, indent = 0):
    """
    Print the ASCII representation of an act tree.
    :param tree: The root of an act tree
    :param indent: the number of characters to indent the tree
    :return: nothing
    """
    for child in printTree.children:
        print "    " * indent, "-->", child.name

        if child.children != []:
            print_act_tree(child, indent + 1)


def printobj(text):
    print text
    return ActStatus.SUCCESS


if __name__ == "__main__":
    tree = Parallel(
        [
            Loop(
                [
                    Wrap(lambda: printobj("Hello 1")),
                    Wrap(lambda: printobj("Hello 2"))
                ], num_iter=10),
            Loop(
                [
                    Wrap(lambda: printobj("Hello 3")),
                    Wrap(lambda: printobj("Hello 4"))
                ], num_iter=5),
        ]
    )
    print_act_tree(tree)

    tree.reset()

    for status in tree.iterator:
        pass
