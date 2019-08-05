import nox

nox.options.reuse_existing_virtualenvs = True
nox.options.error_on_external_run = True


@nox.session(python=('3.5', '3.6', '3.7'))
@nox.parametrize('django', ('2.0', '2.1', '2.2'))
def tests(session, django):
    session.install('poetry')
    session.install(f'django>={django},<{django}.999')
    session.install('factory-boy>=2.9.2,<2.9.99999')
    session.run('poetry', 'install',
                # this is necessary to prevent poetry from creating
                # its own virtualenv
                env={'VIRTUAL_ENV': session.virtualenv.location})
    session.run('pytest')
