# pr_behavior_tree
A simple python behavior tree library using coroutines. Loosely based on [pi_trees](https://github.com/pirobot/pi_trees/), but implements the behaviors as coroutines instead of basic functions.

The main class is called `Act`, and represents an atomic node in the behavior tree. All `Acts` have zero or more children. An `Act` with zero children is a leaf. All `Act`s have a coroutine called `tick`. `tick` returns either `FAIL`, `SUCCESS` or `RUNNING` until it is done ticking, at which point it throws a `StopIteration` exception.

There are special connector `Acts` that update their children in specific ways. `Sequence`, for instance, updates all of its children in order until one of its childen returns `FAIL`. If all the children in a `Sequence` return `SUCCESS`, then the `Sequence` returns `SUCCESS` also. There are other connectors, such as `Select`, which returns `SUCCESS` when any child returns `SUCCESS`, and `PARALLEL`, which calls `tick` on each of its children (more or less) simultaneously until one returns `SUCCESS`. There are other, interesting connectors in the library.

Additionally, any function that returns `SUCCESS` or `FAIL` can be converted into an `Act` merely by using the special `Wrap` `Act`. Note that `lambda` functions can also be converted to an `Act` in the same way.

**How to write an Act**

All you need is a class which extends `Act` and has a `tick` function. The `tick` function, since it is a coroutine, uses the `yield` keyword instead of the `return` keyword to return values. `return` may still be used to break out of the coroutine.

Here's an example act that just prints the numbers 1 through 10:

```python
class Count(Act):
    def __init__(self, children=[], name="Count", *args, **kwargs):
        super(Count, self).__init__(children, name, *args, **kwargs)
    
    def tick(self):
        for i in range(1, 10):
            print i
            # Since we use 'yield' here, the loop does not block the program.
            # yield saves the state of the function so that when it is called again,
            # the program returns to this line, rather than the beginning of the
            # function.
            yield ActStatus.RUNNING
        yield ActStatus.SUCCESS

```

**Example**

Here's an example of a behavior tree and how to use it:
```python
    # Prints an object and returns SUCCESS
    def printobj(text):
        print text
        return ActStatus.SUCCESS
        
    # It's easy to initialize a tree just by specifying the children
    # as a list in the first argument
    tree = Parallel(
        [
            # These loop through their children N times or until one fails
            Loop(
                [
                    # These are an example of how to use
                    # lambdas with the behavior tree
                    Wrap(lambda: printobj("Hello 1")),
                    Wrap(lambda: printobj("Hello 2"))
                ], num_iter=10),
            # This will be run in parallel with the first child
            Loop(
                [
                    Wrap(lambda: printobj("Hello 3")),
                    Wrap(lambda: printobj("Hello 4"))
                ], num_iter=5),
        ]
    )
    # Print an ascii representation of the tree
    print_act_tree(tree)
    
    # Reset the tree's state before running it
    tree.reset()
    
    # Run the tree to completion. Notice that you don't have to block here.
    # You can break out of the loop at any time to do other things, and return
    # to the loop later. If the Act needs to be suspended for a long time, and
    # then resumed later, call "tree.suspend()" followed by "tree.resume()"
    for status in tree.iterator:
        pass
```
        
The output of the test program is:


     --> Loop
         --> Wrap                     Wrap(lambda: printobj("Hello 1")),
    
         --> Wrap                     Wrap(lambda: printobj("Hello 2"))
    
     --> Loop
         --> Wrap                     Wrap(lambda: printobj("Hello 3")),
    
         --> Wrap                     Wrap(lambda: printobj("Hello 4"))
    
    Hello 1
    Hello 3
    Hello 2
    Hello 4
    Hello 1
    Hello 3
    Hello 2
    Hello 4
    Hello 1
    Hello 3
    Hello 2
    Hello 4
    Hello 1
    Hello 3
    Hello 2
    Hello 4
    Hello 1

**Suspending and Resuming**

In addition to ticking, `Acts` can be suspended or resumed. An act can override `suspend` and `resume` to do tasks whenever an act has been temporarily put on hold. Sequential acts `suspend` only the current child, while parallel acts `suspend` all children.

**A Note on Parallelism**

Since `Acts` are *coroutines* and not *threads*, they are never truly run in parallel, and thus can't take advantage of multicore processing. But for the most part, they eliminate the need for threading constructs such as locks. The order of executation is also *deterministic*. It is given by the order of the children in each parallel subtree. For instance, in the example above, we had `Parallel([Sequence([1, 2]), Sequence([3, 4])])` as the tree. The update order is deterministic; it is always a parallel breadth-first traversal of the tree -- `1, 3, 2, 4`. 

A more complicated example with a loop in parallel:

`Parallel([Loop([1, 2], num_iters=2), Sequence([3, 4]), Sequence([5, 6])])` 
the traversal order would be `1, 3, 5, 2, 4, 6, 1, 2`. 

But if we instead had:

`Sequence([Loop([1, 2], num_iters=2), Sequence([3, 4]), Sequence([5, 6])])` 
the traversal order would be `1, 2, 1, 2, 3, 4, 5, 6`. 

