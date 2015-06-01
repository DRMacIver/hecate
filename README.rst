======
Hecate
======

Hecate is a Python 3 library for testing command line interfaces that make
interesting use of the terminal, e.g. through ncurses. Unlike tools like
expect or pexpect it runs a full blown terminal emulator (specifically, tmux)
behind the scenes, so you can take accurate snapshots of what your application
would look like when run by a real user.

Frequently Anticipated Questions
================================

----------------
Are you serious?
----------------

Not very, no. As a concept it works and works well, and I'm fully prepared to
maintain this if it proves popular, but this should be considered a semi
experimental which just happens to be orders of magnitude better than all of
the for serious mature projects you could be using instead.

----------------------------
Will you support Python 2.7?
----------------------------

No

--------
Why not?
--------

Because you shouldn't need it and I don't want to. Hecate scripts are stand
alone applications written green field that interact with your program through
its terminal interface. You can easily test things written in any language you
like, including other versions of Python.

------------------------
Why is it called Hecate?
------------------------

It seemed appropriate to name a Selenium for curses based applications after
`a goddess whose domain includes the moon and magic
<http://en.wikipedia.org/wiki/Hecate>`_.

-----------------
How does it work?
-----------------

Behind the scenes Hecate is spawning a tmux instance and running your command
with it along with a monitoring process so that we can report back the exit
code (after all, who would make a testing framework that didn't report the
standard mechanism for indicating errors back to you?). Hecate interacts with
the tmux server using its command line tools.
