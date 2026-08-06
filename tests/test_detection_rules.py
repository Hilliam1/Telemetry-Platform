from app.detection.rules import BUILTIN_RULES


def test_builtin_rule_ids_are_unique():
    identities = {
        (rule.rule_id, rule.version)
        for rule in BUILTIN_RULES
    }

    assert len(identities) == len(BUILTIN_RULES)


def test_builtin_rules_have_explanations():
    assert all(
        rule.explanation.strip()
        for rule in BUILTIN_RULES
    )


def test_builtin_rules_have_investigation_steps():
    assert all(
        rule.investigation_steps
        for rule in BUILTIN_RULES
    )


def test_builtin_rules_target_sysmon_process_creation():
    assert all(
        rule.source_type == "sysmon"
        and rule.event_id == 1
        for rule in BUILTIN_RULES
    )