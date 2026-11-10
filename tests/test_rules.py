from finance_agent.rules import RuleBook, pattern_for


def test_load_and_match(rules_path):
    book = RuleBook.load(rules_path)
    assert book.match("KPAY*CHAN KEE CAFE HONG KONG HK").category == "Food"
    assert book.match("PAYPAL *ANTHROPIC").category == "Subscriptions"
    assert book.match("MYSTERY MERCHANT LTD") is None


def test_learned_rule_round_trips(tmp_path, rules_path):
    book = RuleBook.load(rules_path)
    book.add(pattern_for("MYSTERY MERCHANT LTD KOWLOON HK"), "Shopping")
    out = tmp_path / "rules.yaml"
    book.save(out)
    reloaded = RuleBook.load(out)
    hit = reloaded.match("MYSTERY MERCHANT LTD KOWLOON HK")
    assert hit.category == "Shopping" and hit.source == "approved"


def test_pattern_for_drops_location_noise():
    assert pattern_for("KPAY*CHAN KEE CAFE HONG KONG HK") == r"KPAY\*CHAN\ KEE\ CAFE"
    assert pattern_for("MYSTERY MERCHANT LTD KOWLOON HK") == r"MYSTERY\ MERCHANT\ LTD"


def test_missing_file_gives_empty_book(tmp_path):
    assert RuleBook.load(tmp_path / "nope.yaml").rules == []
