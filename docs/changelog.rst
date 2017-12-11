Changelog
=========

0.2
===

- Renamed ``bridgekeeper.registry.registry`` to :data:`bridgekeeper.perms`.
- Renamed ``bridgekeeper.predicates.Predicate.apply()`` to :meth:`~bridgekeeper.predicates.Predicate.check`
- Changed :meth:`bridgekeeper.predicates.Predicate.filter` so that it takes the user object as the first argument, for consistency with the rest of the library (i.e. it's singnature went from ``filter(queryset, user)`` to ``filter(user, queryset)``).
