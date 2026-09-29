# Conventions for every skill

- **One job per skill.** A skill never invokes another skill. It reads artifacts and writes artifacts, as declared in its skill.yml; tasks decide the order.
- **Definitions come from EXACT.GOVERNANCE.** Revenue = P&L accounts of revenue type (BalanceType W, Type 110), sign flipped. Every answer names the definition and its DICT_VERSION.
- **Thresholds come from governance/settings.yml.** Never invent one. If a setting is TBD, skip and say so.
- **Amounts** in EUR, two decimals, as signed in Exact (debit positive) unless a view says otherwise.
- **Customer code** = Exact relation number = Striker customer code = Bumbal code.
- **Levels of action** (plan section 7): 0 report (agent alone), 1 propose (change request; bookkeeper applies), 2 structural (recommend only; a person with Exact admin rights decides).
- **The agent never writes to Exact.** Not through the loader, not through Claude's Exact connector, not by asking another agent to.
