# pr_behavior_tree
A simple python behavior tree library based on coroutines. 

The main class is called `Act`, and represents an atomic node in the behavior tree. All `Act`s have zero or more children. An `Act` with zero children is a leaf. All `Act`s have a coroutine called `tick`. `tick` returns either `FAIL`, `SUCCESS` or `RUNNING` until it is done ticking, at which point it throws a `StopIteration` exception.

There are special connector `Act`s that update their children in specific ways. `Sequence`, for instance, updates all of its children in order until one of its childen returns `FAIL`. If all the children in a `Sequence` return `SUCCESS`, then the `Sequence` returns `SUCCESS` also. There are other connectors, such as `Select`, which returns `SUCCESS` when any child returns `SUCCESS`, and `PARALLEL`, which calls `tick` on each of its children (more or less) simultaneously until one returns `SUCCESS`. There are other, interesting connectors in the library.

Additionally, any function that returns `SUCCESS` or `FAIL` can be converted into an `Act` merely by using the special `Wrap` `Act`. Note that `lambda` functions can also be converted to an `Act` in the same way.

**Example**

Here's an example of a behavior tree and how to use it:

    # Prints an object and returns SUCCESS
    def printobj(text):
        print text
        return ActStatus.SUCCESS
        
    # It's easy to initialize a tree just by specifying the children as a list in the first argument
    tree = Parallel(
        [
            # These loop through their children N times or until one fails
            Loop(
                [
                    # These are an example of how to use lambdas with the behavior tree
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
    
    # Run the tree to completion
    for status in tree.iterator:
        pass
        
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

