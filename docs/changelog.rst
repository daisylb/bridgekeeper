Changelog
=========

0.3
---

- Renamed **predicates** to **rules**, because the latter is a more accessible term that describe the concept just as well. Besides, "permissions are made up of rules" sounds a lot better than "permissions are made up of predicates".
- Renamed **ambient predicates** to **blanket rules**, because it's a more descriptive name. Note that the ``@ambient`` decorator is now called ``@blanket_rule``, because having a ``@blanket`` decorator would be weird.

0.2
---

- Renamed ``bridgekeeper.registry.registry`` to :data:`bridgekeeper.perms`.
- Renamed ``bridgekeeper.predicates.Predicate.apply()`` to :meth:`~bridgekeeper.predicates.Predicate.check`
- Changed :meth:`bridgekeeper.predicates.Predicate.filter` so that it takes the user object as the first argument, for consistency with the rest of the library (i.e. it's singnature went from ``filter(queryset, user)`` to ``filter(user, queryset)``).
