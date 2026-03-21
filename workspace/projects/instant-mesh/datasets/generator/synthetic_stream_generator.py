import argparse
import json
import random
import uuid
from datetime import datetime, timedelta
from pathlib import Path

SCENARIOS = {
    "legit": 0.8,
    "app_scam": 0.05,
    "mule_network": 0.05,
    "sanction_hit": 0.05,
    "velocity_abuse": 0.05,
}

COUNTRIES = ["DK", "DE", "NL", "SE", "FI", "NO", "ES", "IT"]
CURRENCIES = ["EUR", "DKK", "SEK", "NOK"]
MERCHANT_CATEGORIES = ["GDDS", "CASHM", "SERV", "TRVL", "UTIL"]


def random_iban(country: str) -> str:
    digits = "".join(str(random.randint(0, 9)) for _ in range(14))
    return f"{country}{random.randint(10, 99)}{digits}"


def random_bic(country: str) -> str:
    letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    bic = "".join(random.choice(letters) for _ in range(6))
    branch = "".join(random.choice(letters) for _ in range(3))
    return f"{bic}{country}{branch}"


def build_event(timestamp: datetime, scenario: str) -> dict:
    payer_country = random.choice(COUNTRIES)
    payee_country = random.choice(COUNTRIES)
    currency = random.choice(CURRENCIES)

    base_amount = random.uniform(25, 2000)
    if scenario == "app_scam":
        amount = base_amount * random.uniform(1.5, 3.0)
    elif scenario == "mule_network":
        amount = base_amount * random.uniform(0.5, 1.2)
    elif scenario == "sanction_hit":
        amount = base_amount
    elif scenario == "velocity_abuse":
        amount = base_amount * random.uniform(0.8, 1.5)
    else:
        amount = base_amount

    event_id = str(uuid.uuid4())
    payer_iban = random_iban(payer_country)
    payee_iban = random_iban(payee_country)

    return {
        "event_id": event_id,
        "created_at": timestamp.isoformat() + "Z",
        "scenario": scenario,
        "payment": {
            "amount": round(amount, 2),
            "currency": currency,
            "category": random.choice(MERCHANT_CATEGORIES),
            "service_level": "SCTInst",
            "priority": "HIGH",
        },
        "payer": {
            "iban": payer_iban,
            "bic": random_bic(payer_country),
            "country": payer_country,
        },
        "payee": {
            "iban": payee_iban,
            "bic": random_bic(payee_country),
            "country": payee_country,
        },
        "flags": build_flags(scenario, payer_iban, payee_iban),
    }


def build_flags(scenario: str, payer_iban: str, payee_iban: str) -> dict:
    if scenario == "app_scam":
        return {
            "description": "High-value rush payment to new payee",
            "features": ["new_payee", "amount_spike", "merchant_mismatch"],
        }
    if scenario == "mule_network":
        return {
            "description": "Payee linked to >5 unique senders in 24h window",
            "features": ["fan_in", "network_degree"],
        }
    if scenario == "sanction_hit":
        return {
            "description": "Payee IBAN matched synthetic sanction list entry",
            "features": ["sanction_list_match"],
            "watchlist_match": payee_iban[-6:],
        }
    if scenario == "velocity_abuse":
        return {
            "description": "Payer sent >10 instant payments in <60 min",
            "features": ["burst_activity", "velocity"]
        }
    return {
        "description": "No anomalies",
        "features": [],
    }


def weighted_scenario_choice(custom_weights):
    roll = random.random()
    cumulative = 0.0
    for scenario, weight in custom_weights.items():
        cumulative += weight
        if roll <= cumulative:
            return scenario
    return list(custom_weights.keys())[-1]


def main():
    parser = argparse.ArgumentParser(description="Generate synthetic instant-payment streams")
    parser.add_argument("--rows", type=int, default=10000)
    parser.add_argument("--seed", type=int, default=1337)
    parser.add_argument("--out", type=str, default="data/streams/demo.jsonl")
    parser.add_argument("--scenarios", nargs="*", default=list(SCENARIOS.keys()))
    args = parser.parse_args()

    random.seed(args.seed)

    weights = {k: SCENARIOS[k] for k in args.scenarios if k in SCENARIOS}
    total = sum(weights.values())
    weights = {k: v / total for k, v in weights.items()}

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    start_time = datetime.utcnow() - timedelta(hours=1)
    delta = timedelta(milliseconds=100)

    with out_path.open("w", encoding="utf-8") as f:
        for i in range(args.rows):
            scenario = weighted_scenario_choice(weights)
            event = build_event(start_time + i * delta, scenario)
            f.write(json.dumps(event) + "\n")

    print(f"Wrote {args.rows} events to {out_path}")


if __name__ == "__main__":
    main()
