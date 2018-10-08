## Making Changes
tl;dr: Contributors should follow the standard team development practices.

* Fork the repository on GitHub.
* Create a topic branch from where you want to base your work.
* This is usually the master branch.
* Please avoid working directly on master branch.
* Make commits of logical units (if needed rebase your feature branch before submitting it).
* Check for unnecessary whitespace with git diff --check before committing.
* Make sure your commit messages are in the proper format.
* If your commit fixes an open issue, reference it in the commit message (#15).
* Make sure your code comforms to [PEP8](https://www.python.org/dev/peps/pep-0008/).
* Make sure you have added the necessary tests for your changes.
* Run all the tests to assure nothing else was accidentally broken.


It is highly encouraged to follow this link and understand git branching model explained in it: http://nvie.com/posts/a-successful-git-branching-model

## Submitting Changes

* Push your changes to a topic branch in your fork of the repository.
* Submit a Pull Request.
* Wait for maintainer feedback.


## Dont' know where to start? 
There are usually several TODO comments scattered around the codebase, maybe
check them out and see if you have ideas, or can help with them. Also, check
the [open issues](https://github.com/muatik/flask-profiler/issues) in case there's something that sparks your interest. What
about documentation?  I suck at english so if you're fluent with it (or notice
any error), why not help with that? 
