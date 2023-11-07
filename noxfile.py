import nox

nox.options.sessions = ("tests",)
nox.options.reuse_existing_virtualenvs = True
nox.options.error_on_external_run = True


@nox.session(python=("3.8", "3.9", "3.10", "3.11", "3.12"))
@nox.parametrize("django", ("3.2", "4.2"))
def tests(session, django):
    session.install("poetry")
    session.run(
        "poetry",
        "install",
        # this is necessary to prevent poetry from creating
        # its own virtualenv
        env={"VIRTUAL_ENV": session.virtualenv.location},
    )
    session.install(f"django>={django},<{django}.999")
    session.run("pytest")


@nox.session(python="3.12")
def docs(session):
    session.install("poetry")
    session.run(
        "poetry",
        "install",
        # this is necessary to prevent poetry from creating
        # its own virtualenv
        env={"VIRTUAL_ENV": session.virtualenv.location},
    )

    session.run("sphinx-build", "docs", "docs/_build/html")


@nox.session(python=False)
def clean_docs(session):
    session.run("rm", "-rf", "docs/_build")


@nox.session(python="3.12")
def release_test(session):
    session.install("poetry", "twine")
    session.run(
        "poetry",
        "build",
        # this is necessary to prevent poetry from creating
        # its own virtualenv
        env={"VIRTUAL_ENV": session.virtualenv.location},
    )
    session.run("twine", "check", "dist/*")
