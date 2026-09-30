"""Synthetic labelled narrations in the formats of SBI, HDFC, ICICI, Axis, Kotak, PSU and short app exports."""

import math
import random
import re
import string

from mykhata_ml import catalog as C
from mykhata_ml.categories import CATEGORIES

BANK_STYLES = {"SBI": 22, "HDFC": 20, "ICICI": 16, "AXIS": 12, "KOTAK": 8, "PSU": 10, "SHORT": 12}

CHANNEL_MODE = {
    "upi": "UPI", "card_pos": "CARD", "card_ecom": "CARD", "card_si": "CARD", "neft": "NEFT",
    "imps": "IMPS", "ach": "ACH", "atm": "ATM", "billpay": "OTHERS", "cheque": "CHEQUE",
    "raw": "OTHERS", "special": "OTHERS",
}

# category -> [(weight, channel, counterparty_kind)]
# counterparty kinds: merchant (catalogue), local (small shop), person, employer, special
RECIPES = {
    "FOOD_DINING":      [(45, "upi", "merchant"), (30, "upi", "local"), (8, "card_pos", "merchant"),
                         (7, "card_pos", "local"), (5, "card_ecom", "merchant"), (5, "raw", "merchant")],
    "GROCERIES":        [(30, "upi", "merchant"), (40, "upi", "local"), (12, "card_pos", "merchant"),
                         (8, "card_pos", "local"), (5, "card_ecom", "merchant"), (5, "raw", "merchant")],
    "SHOPPING":         [(30, "upi", "merchant"), (25, "card_ecom", "merchant"), (10, "card_pos", "merchant"),
                         (15, "upi", "local"), (10, "card_pos", "local"), (5, "raw", "merchant"),
                         (5, "billpay", "merchant")],
    "TRANSPORT":        [(55, "upi", "merchant"), (12, "card_ecom", "merchant"), (15, "upi", "local"),
                         (10, "card_pos", "merchant"), (8, "raw", "merchant")],
    "FUEL":             [(35, "upi", "merchant"), (25, "upi", "local"), (20, "card_pos", "merchant"),
                         (10, "card_pos", "local"), (10, "raw", "merchant")],
    "TRAVEL":           [(45, "upi", "merchant"), (30, "card_ecom", "merchant"), (10, "card_pos", "merchant"),
                         (10, "raw", "merchant"), (5, "neft", "merchant")],
    "BILLS_UTILITIES":  [(40, "upi", "merchant"), (30, "billpay", "merchant"), (5, "card_si", "merchant"),
                         (10, "ach", "merchant"), (10, "raw", "merchant"), (5, "upi", "local")],
    "RENT":             [(45, "upi", "person"), (20, "neft", "person"), (10, "imps", "person"),
                         (15, "upi", "merchant"), (10, "cheque", "person")],
    "ENTERTAINMENT":    [(30, "card_si", "merchant"), (35, "upi", "merchant"), (20, "card_ecom", "merchant"),
                         (10, "raw", "merchant"), (5, "upi", "local")],
    "HEALTH":           [(35, "upi", "local"), (25, "upi", "merchant"), (15, "card_pos", "merchant"),
                         (10, "card_pos", "local"), (10, "card_ecom", "merchant"), (5, "raw", "merchant")],
    "EDUCATION":        [(20, "upi", "merchant"), (20, "neft", "local"), (20, "upi", "local"),
                         (20, "card_ecom", "merchant"), (10, "billpay", "local"), (10, "ach", "merchant")],
    "PERSONAL_CARE":    [(30, "upi", "merchant"), (40, "upi", "local"), (15, "card_pos", "local"),
                         (10, "card_si", "merchant"), (5, "raw", "merchant")],
    "INSURANCE":        [(40, "ach", "merchant"), (25, "upi", "merchant"), (15, "card_ecom", "merchant"),
                         (10, "billpay", "merchant"), (10, "raw", "merchant")],
    "BANK_CHARGES":     [(100, "special", "special")],
    "EMI_LOAN":         [(55, "ach", "merchant"), (10, "upi", "merchant"), (25, "special", "special"),
                         (10, "neft", "merchant")],
    "CREDIT_CARD_BILL": [(30, "upi", "merchant"), (25, "billpay", "merchant"), (10, "neft", "merchant"),
                         (25, "special", "special"), (10, "imps", "merchant")],
    "INVESTMENT":       [(40, "ach", "merchant"), (25, "upi", "merchant"), (10, "neft", "merchant"),
                         (25, "special", "special")],
    "CASH_WITHDRAWAL":  [(85, "atm", "special"), (15, "special", "special")],
    "TRANSFER_OUT":     [(75, "upi", "person"), (12, "imps", "person"), (10, "neft", "person"),
                         (3, "cheque", "person")],
    "TRANSFER_IN":      [(75, "upi", "person"), (12, "imps", "person"), (10, "neft", "person"),
                         (3, "cheque", "person")],
    "SELF_TRANSFER":    [(100, "special", "special")],
    "SALARY":           [(55, "neft", "employer"), (10, "ach", "employer"), (10, "imps", "employer"),
                         (25, "special", "special")],
    "INTEREST":         [(100, "special", "special")],
    "INVESTMENT_RETURN": [(100, "special", "special")],
    "REFUND_CASHBACK":  [(100, "special", "special")],
    "OTHER":            [(100, "special", "special")],
}

# (low, high) log-uniform range; MENUS are common exact prices.
AMOUNTS = {
    "FOOD_DINING": (40, 3000), "GROCERIES": (20, 6000), "SHOPPING": (99, 40000),
    "TRANSPORT": (10, 1500), "FUEL": (100, 5000), "TRAVEL": (250, 45000),
    "BILLS_UTILITIES": (99, 6000), "RENT": (4000, 65000), "ENTERTAINMENT": (49, 2500),
    "HEALTH": (40, 25000), "EDUCATION": (300, 90000), "PERSONAL_CARE": (100, 6000),
    "INSURANCE": (436, 60000), "BANK_CHARGES": (1, 1200), "EMI_LOAN": (999, 65000),
    "CREDIT_CARD_BILL": (300, 90000), "INVESTMENT": (100, 60000), "CASH_WITHDRAWAL": (100, 20000),
    "TRANSFER_OUT": (1, 50000), "TRANSFER_IN": (1, 50000), "SELF_TRANSFER": (500, 150000),
    "SALARY": (12000, 300000), "INTEREST": (1, 9000), "INVESTMENT_RETURN": (20, 150000),
    "REFUND_CASHBACK": (1, 25000), "OTHER": (1, 10000),
}
MENUS = {
    "BILLS_UTILITIES": [19, 99, 149, 155, 179, 199, 239, 249, 299, 349, 399, 449, 479, 499, 599,
                        666, 719, 799, 839, 859, 999, 1199, 1799, 2999, 3599, 853, 903, 1103],
    "ENTERTAINMENT": [59, 99, 119, 129, 149, 179, 199, 299, 399, 499, 649, 899, 999, 1499, 1499],
    "BANK_CHARGES": [5.9, 11.8, 17.7, 20.0, 23.6, 29.5, 59.0, 88.5, 100.0, 118.0, 177.0, 236.0,
                     295.0, 354.0, 500.0, 590.0, 885.0, 1180.0],
}
FIXED_AMOUNTS = {"PMJJBY": [436.0], "PMSBY": [20.0]}  # govt insurance schemes, auto-debited yearly
ROUND_TO = {"RENT": 500, "SALARY": 1, "INVESTMENT": 500, "CASH_WITHDRAWAL": 100, "EMI_LOAN": 1,
            "SELF_TRANSFER": 500, "FUEL": 50}


def _compact(s):
    return re.sub(r"[^A-Za-z0-9]", "", s)


class NarrationGenerator:
    def __init__(self, seed=42, popularity=0.7):
        """popularity: Zipf exponent over each category's catalogue order (big brands are listed first)."""
        self.r = random.Random(seed)
        self._merchants = C.MERCHANTS
        self._weights = {cat: [1 / (i + 1) ** popularity for i in range(len(entries))]
                         for cat, entries in C.MERCHANTS.items()}

    def pick(self, seq):
        return self.r.choice(seq)

    def wpick(self, pairs):
        """Pick from [(weight, *rest)] and return rest (or the single item)."""
        total = sum(p[0] for p in pairs)
        x = self.r.uniform(0, total)
        for p in pairs:
            x -= p[0]
            if x <= 0:
                return p[1:] if len(p) > 2 else p[1]
        return pairs[-1][1:] if len(pairs[-1]) > 2 else pairs[-1][1]

    def chance(self, p):
        return self.r.random() < p

    def digits(self, n):
        return "".join(self.r.choice(string.digits) for _ in range(n))

    def alnum(self, n, upper=True):
        pool = string.ascii_uppercase + string.digits if upper else string.ascii_lowercase + string.digits
        return "".join(self.r.choice(pool) for _ in range(n))

    def trunc(self, s, lo, hi):
        return s[: self.r.randint(lo, hi)]

    def rrn(self):  # 12-digit UPI reference
        return self.pick("3456") + self.digits(11)

    def utr(self, code):
        return f"{code}{self.pick('NRH')}{self.digits(self.r.choice([11, 12, 13]))}"

    def bank(self):
        return self.pick(C.BANKS)

    def ifsc(self, code):
        return f"{code}0{self.digits(6) if self.chance(0.7) else self.alnum(6)}"

    def card(self):
        bins = ["416021", "459150", "524193", "438628", "652150", "508227", "607153", "421323"]
        return f"{self.pick(bins)}XXXXXX{self.digits(4)}" if self.chance(0.7) else f"XXXXXXXXXXXX{self.digits(4)}"

    def ddmm(self):
        return f"{self.r.randint(1, 28):02d}{self.r.randint(1, 12):02d}"

    def date_str(self):
        return f"{self.r.randint(1, 28):02d}-{self.r.randint(1, 12):02d}-{self.r.choice([23, 24, 25, 26])}"

    def acct(self):
        return self.digits(self.r.choice([10, 11, 12, 14]))

    def merchant(self, cat):
        entry = self.r.choices(self._merchants[cat], weights=self._weights[cat])[0]
        alias = entry[0] if self.chance(0.4) else self.pick(entry)
        slug = _compact(self.pick(entry)).lower()[:14]
        vpa = self.pick([
            f"{slug}@{self.pick(C.MERCHANT_HANDLES)}",
            f"{slug}.{self.pick(['payu', 'rzp', 'razorpay', 'bd', 'cf', 'upi'])}@{self.pick(C.MERCHANT_HANDLES)}",
            f"{slug}{self.digits(self.r.randint(2, 6))}@{self.pick(C.MERCHANT_HANDLES)}",
            f"{slug}online@{self.pick(C.MERCHANT_HANDLES)}",
        ])
        return {"name": alias, "vpa": vpa, "id": entry[0], "kind": "merchant"}

    def local(self, cat):
        name = f"{self.pick(C.LOCAL_PREFIXES)} {self.pick(C.LOCAL_SUFFIXES[cat])}"
        if self.chance(0.15):
            name += f" {self.pick(C.CITIES)}"
        vpa = self.pick([
            f"paytmqr{self.digits(10)}{self.alnum(4, upper=False)}@paytm",
            f"bharatpe.{self.digits(10)}@fbpe",
            f"bharatpe{self.digits(8)}@yesbankltd",
            f"q{self.digits(9)}@ybl",
            f"{_compact(name).lower()[:12]}@okbizaxis",
            f"{_compact(name).lower()[:12]}{self.digits(3)}@okbizicici",
            f"{self.pick('6789')}{self.digits(9)}@{self.pick(C.PERSON_HANDLES)}",
            f"gpay-{self.digits(11)}@okbizaxis",
            f"mab.{self.digits(15)}@axisbank",
        ])
        display = name
        if self.chance(0.08):  # QR registered in the shop-owner's personal name
            display = self.person()["name"]
        return {"name": display, "vpa": vpa, "id": f"LOCAL:{name}", "kind": "local"}

    def person(self):
        f, l = self.pick(C.FIRST_NAMES), self.pick(C.LAST_NAMES)
        name = self.wpick([
            (45, f"{f} {l}"), (15, f"{f} {self.pick(C.FIRST_NAMES)} {l}"), (10, f"{f} {l[0]}"),
            (8, f"{l} {f}"), (7, f"MR {f} {l}"), (5, f"MRS {f} {l}"), (10, f),
        ])
        vpa = self.wpick([
            (30, f"{f.lower()}{l.lower()}@{self.pick(C.PERSON_HANDLES)}"),
            (20, f"{f.lower()}.{l.lower()}{self.digits(self.r.randint(0, 3))}@{self.pick(C.PERSON_HANDLES)}"),
            (30, f"{self.pick('6789')}{self.digits(9)}@{self.pick(C.PERSON_HANDLES)}"),
            (20, f"{f.lower()}{self.digits(self.r.randint(1, 4))}@{self.pick(C.PERSON_HANDLES)}"),
        ])
        if self.chance(0.4):
            name = name.title()
        return {"name": name, "vpa": vpa, "id": "PERSON", "kind": "person"}

    def employer(self):
        if self.chance(0.6):
            name = self.pick(C.EMPLOYERS)
        else:
            name = f"{self.pick(C.LOCAL_PREFIXES)} {self.pick(C.EMPLOYER_SMALL_SUFFIX)}"
        return {"name": name, "vpa": f"{_compact(name).lower()[:12]}@{self.pick(C.MERCHANT_HANDLES)}",
                "id": f"EMPLOYER:{name}", "kind": "employer"}

    def counterparty(self, cat, kind):
        if kind == "merchant":
            return self.merchant(cat)
        if kind == "local":
            return self.local(cat)
        if kind == "person":
            return self.person()
        if kind == "employer":
            return self.employer()
        raise ValueError(kind)

    def note_for(self, cat, cp):
        pool = C.CATEGORY_NOTES.get(cat)
        p_specific = 0.55 if cp["kind"] == "person" else 0.25
        if cat == "RENT":
            p_specific = 0.8
        if pool and self.chance(p_specific):
            n = self.pick(pool)
            if cat == "RENT" and self.chance(0.4):
                n += f" {self.pick(C.MONTHS)}"
            return n
        return self.pick(C.GENERIC_NOTES)

    def ch_upi(self, st, cp, dr, note):
        ref, NAME, vpa = self.rrn(), cp["name"].upper(), cp["vpa"]
        bname, code = self.bank()
        p2p = cp["kind"] == "person"
        d = "DR" if dr else "CR"
        if st in ("SBI", "PSU"):
            core = (f"UPI/{d}/{ref}/{self.trunc(NAME, 6, 20)}/{code}/"
                    f"{self.trunc(vpa, 8, 25)}/{self.trunc(note, 4, 12)}")
            if st == "SBI" and self.chance(0.6):
                core = ("TO TRANSFER-" if dr else "BY TRANSFER-") + core
            return core
        if st == "HDFC":
            return f"UPI-{NAME}-{vpa}-{self.ifsc(code)}-{ref}-{note.upper()}"
        if st == "ICICI":
            nm = cp["name"] if self.chance(0.5) else NAME
            if self.chance(0.5):
                return f"UPI/{ref}/{note}/{vpa}/{bname.title()}/ICI{self.alnum(29)}"[:110]
            return f"UPI/{nm}/{vpa}/{note}/{bname.title()}/{ref}/ICI{self.alnum(20)}"[:110]
        if st == "AXIS":
            return f"UPI/{'P2A' if p2p else 'P2M'}/{ref}/{NAME}/{note}/{bname}"
        if st == "KOTAK":
            if self.chance(0.3):
                return f"{'Sent' if dr else 'Received'} UPI {'to' if dr else 'from'} {cp['name']} {vpa}"
            return f"UPI/{NAME}/{ref}/{note}"
        # SHORT
        token = _compact(NAME)
        return self.pick([f"UPI/{token}", f"UPI/{token[: self.r.randint(4, 12)]}", f"UPI/{NAME}",
                          f"UPI/{token}{self.alnum(self.r.randint(1, 3), upper=False)}"])

    def ch_card_pos(self, st, cp, dr, note, ecom=False, si=False):
        NAME, card = cp["name"].upper(), self.card()
        last4, city = card[-4:], self.pick(C.CITIES)
        if si:
            return self.pick({
                "HDFC": [f"ME DC SI {card} {NAME}", f"DC SI {card} {NAME}"],
                "SBI": [f"SI-{NAME}-{self.digits(10)}", f"BY DEBIT CARD-OTHPG SI {self.digits(12)}{NAME}"],
                "PSU": [f"SI/{NAME}/{self.digits(10)}"],
                "ICICI": [f"SI/{NAME}/{self.digits(12)}", f"MANDATE/{NAME}/{last4}"],
                "AXIS": [f"ECOM SI/{NAME}/{self.date_str()}", f"SI/{NAME}/{last4}"],
                "KOTAK": [f"PCI SI/{last4}/{NAME}", f"SI {NAME} {self.digits(8)}"],
                "SHORT": [NAME, f"{NAME} SUBSCRIPTION"],
            }[st])
        if ecom:
            return self.pick({
                "HDFC": [f"POS {card} {NAME}", f"ECOM {card} {NAME}", f"POS {card} {NAME} ONLINE"],
                "SBI": [f"BY DEBIT CARD-OTHPG {self.digits(12)}{NAME}", f"POS ATM PURCH OTHPG {self.digits(10)}/{NAME}"],
                "PSU": [f"ECOM/{NAME}/{self.digits(10)}", f"POS/PG/{NAME}"],
                "ICICI": [f"ECOM PUR/{NAME}/{self.digits(12)}", f"PCI/{last4}/{NAME}/{self.digits(12)}"],
                "AXIS": [f"ECOM PUR/{NAME}/{self.r.randint(0, 23):02d}:{self.r.randint(0, 59):02d}/{self.date_str()}"],
                "KOTAK": [f"PCI/{last4}/{NAME}/{self.digits(12)}"],
                "SHORT": [NAME, f"{NAME} ONLINE"],
            }[st])
        return self.pick({
            "HDFC": [f"POS {card} {NAME} {city}", f"POS REF {card}-{self.ddmm()} {NAME}"],
            "SBI": [f"POS ATM PURCH OTHPOS{self.digits(10)}/{NAME}", f"POS PRCH {NAME} {city}",
                    f"BY DEBIT CARD-OTHPOS{self.digits(10)}{NAME}{city}"],
            "PSU": [f"POS/{NAME}/{city}/{self.digits(6)}", f"POS {NAME} {city}"],
            "ICICI": [f"PCD/{last4}/{NAME}/{city}/{self.digits(6)}", f"PCD/{last4}/{NAME}/{city}"],
            "AXIS": [f"POS/{NAME}/{city}/{self.date_str()}/{self.r.randint(0, 23):02d}:{self.r.randint(0, 59):02d}"],
            "KOTAK": [f"PCD/{last4}/{NAME}/{city}", f"PCD/{last4}/{NAME}/{city}/{self.digits(6)}"],
            "SHORT": [NAME, f"{NAME} {city}"],
        }[st])

    def ch_neft(self, st, cp, dr, note):
        NAME = cp["name"].upper()
        _, code = self.bank()
        utr, ifsc = self.utr(code), self.ifsc(code)
        holder = f"{self.pick(C.FIRST_NAMES)} {self.pick(C.LAST_NAMES)}"
        if st == "SBI":
            return f"{'TO' if dr else 'BY'} TRANSFER-NEFT*{ifsc}*{utr}*{NAME}*{note}"
        if st == "PSU":
            return f"NEFT/{'DR' if dr else 'CR'}/{utr}/{NAME}/{code}"
        if st == "HDFC":
            if dr:
                return f"NEFT DR-{ifsc}-{NAME}-NETBANK, MUM-{utr}-{note.upper()}"
            return f"NEFT CR-{ifsc}-{NAME}-{holder}-{utr}{('-' + note.upper()) if note else ''}"
        if st == "ICICI":
            if self.chance(0.5):
                return f"NEFT-{utr}-{NAME}-{note}-{self.acct()}-{ifsc}"
            return f"INF/NEFT/{utr}/{ifsc}/{NAME}"
        if st == "AXIS":
            return f"NEFT/{utr}/{NAME}/{self.bank()[0]}/{note}"
        if st == "KOTAK":
            return f"NEFT {utr} {NAME} {note}"
        return self.pick(["NEFT", f"NEFT {NAME}", f"NEFT/{NAME}", f"NEFT {note}"])

    def ch_imps(self, st, cp, dr, note):
        NAME, ref = cp["name"].upper(), self.digits(12)
        bname, code = self.bank()
        if st == "SBI":
            return f"{'TO' if dr else 'BY'} TRANSFER-IMPS/{ref}/{self.trunc(NAME, 8, 20)}/{code}"
        if st == "PSU":
            return f"IMPS/{'DR' if dr else 'CR'}/{ref}/{NAME}"
        if st == "HDFC":
            return f"IMPS-{ref}-{NAME}-{code}-XXXXXXXX{self.digits(4)}-{note.upper()}"
        if st == "ICICI":
            return f"MMT/IMPS/{ref}/{note}/{NAME}/{bname.title()}"
        if st == "AXIS":
            return f"IMPS/P2A/{ref}/{NAME}/{bname}/{note}"
        if st == "KOTAK":
            return f"IMPS/{ref}/{NAME}"
        return self.pick(["IMPS", f"IMPS {NAME}", f"IMPS/{ref}/{NAME}"])

    def ch_ach(self, st, cp, dr, note):
        NAME = cp["name"].upper()
        umrn = f"{self.pick(['HDFC', 'ICIC', 'SBIN', 'UTIB', 'KKBK', 'BARB'])}{self.digits(16)}"
        ref = self.alnum(self.r.randint(8, 14))
        if st == "SBI":
            return f"{'DEBIT-ACHDr' if dr else 'CREDIT-ACHCr'} {umrn} {NAME}"
        if st == "PSU":
            return f"{'ECS DR' if dr else 'ECS CR'}/{NAME}/{ref}"
        if st == "HDFC":
            return f"{'ACH D-' if dr else 'ACH C-'} {NAME}-{ref}{(' ' + note.upper()) if note and not dr else ''}"
        if st == "ICICI":
            return self.pick([f"ACH/{NAME}/{ref}", f"NACH/{NAME}/{umrn}"])
        if st == "AXIS":
            return f"{'NACH-DR' if dr else 'NACH-CR'}-{NAME}-{umrn}"
        if st == "KOTAK":
            return f"NACH-{NAME}-{ref}"
        return self.pick([f"NACH {NAME}", f"ACH {NAME}", f"ACH/{NAME}"])

    def ch_billpay(self, st, cp, dr, note):
        NAME, ref = cp["name"].upper(), self.digits(self.r.randint(8, 12))
        consumer = self.digits(self.r.randint(8, 12))
        return self.pick({
            "HDFC": [f"BILLPAY-{NAME}-{ref}", f"IB BILLPAY DR-{_compact(NAME)[:6]}-{consumer}"],
            "SBI": [f"BBPS/{NAME}/{ref}", f"TO TRANSFER-INB {NAME} BILL PAYMENT {ref}"],
            "PSU": [f"BBPS/{NAME}/{consumer}", f"BILL PAY {NAME}"],
            "ICICI": [f"BIL/BPAY/{ref}/{NAME}/{consumer}", f"BIL/ONL/{ref}/{NAME}/{consumer}"],
            "AXIS": [f"BBPS/{ref}/{NAME}", f"BILLPAY/{NAME}/{consumer}"],
            "KOTAK": [f"BBPS-{NAME}-{ref}"],
            "SHORT": [f"{NAME} BILL PAYMENT", f"BBPS {NAME}"],
        }[st])

    def ch_cheque(self, st, cp, dr, note):
        NAME, chq = cp["name"].upper(), self.digits(6)
        bname = self.bank()[0]
        if dr:
            return self.pick({
                "HDFC": [f"CHQ PAID-MICR INWARD CLEARING-{NAME}-{bname}"],
                "SBI": [f"TO CLEARING-{NAME}", f"CHQ TRANSFER-{chq}-{NAME}"],
                "PSU": [f"CLG/{chq}/{NAME}"], "ICICI": [f"CLG/{NAME}/{chq}/{bname.title()}"],
                "AXIS": [f"CLG/{chq}/{NAME}"], "KOTAK": [f"CHQ {chq} {NAME}"], "SHORT": [f"CHQ {chq}"],
            }[st])
        return self.pick([f"CHQ DEP - MICR CLG - {bname}", f"BY CLEARING-{chq}", f"CLG/{NAME}/{chq}",
                          f"INWARD CLG {chq} {NAME}", f"CHQ {chq}"])

    def ch_atm(self, st):
        city, card = self.pick(C.CITIES), self.card()
        atm_id = self.pick(["S1", "S2", "SPCN", "DC", "NWD", "APN"]) + self.alnum(6)
        return self.pick({
            "SBI": [f"ATM WDL-ATM CASH {self.digits(4)} {city}", f"ATM WDL-{atm_id} {city}"],
            "PSU": [f"ATM/{city}/{self.digits(6)}", f"CASH WDL ATM {atm_id}"],
            "HDFC": [f"NWD-{card}-{atm_id}-{city}", f"EAW-{card}-{atm_id}-{city}"],
            "ICICI": [f"ATM/CASH/{self.digits(6)}/{city}", f"CAW/{card[-4:]}/{atm_id}/{city}"],
            "AXIS": [f"ATM-CASH-AXIS/{city}/{self.date_str()}", f"ATM-CASH/{atm_id}/{city}"],
            "KOTAK": [f"ATL/{card[-4:]}/{self.digits(6)}/{city}", f"ATW/{card[-4:]}/{city}"],
            "SHORT": ["ATM", "ATM WDL", "CASH WITHDRAWAL", f"ATM {city}"],
        }[st])

    def ch_raw(self, st, cp, dr, note):
        NAME = cp["name"].upper()
        return self.pick([NAME, NAME, _compact(NAME)[:12], f"{NAME} {self.digits(6)}",
                          f"{NAME} {self.pick(C.CITIES)}", f"{_compact(NAME)[:12]}/"])

    def self_name(self):
        return f"{self.pick(C.FIRST_NAMES)} {self.pick(C.LAST_NAMES)}"

    def sp_BANK_CHARGES(self, st, dr):
        q = f"{self.pick(C.MONTHS)}{self.r.randint(23, 26)}"
        items = [f"SMS CHARGES FOR QTR {q}", "SMS ALERT CHGS", "DEBIT CARD ANNUAL FEE", "DC AMC CHGS",
                 "ATM DECL CHGS", "CHRG: ATM TXN BEYOND LIMIT", "GST @18% ON CHARGES", "IGST ON CHGS",
                 "MIN BAL CHGS", "NON MAINTENANCE OF AVG BAL", "IMPS CHARGES", "NEFT CHGS",
                 "CHQ BOOK ISSUE CHGS", "ECS RTN CHGS", "ACH DEBIT RETURN CHARGES",
                 f"CONSOLIDATED CHARGES FOR A/C {self.acct()}", "CARD REPLACEMENT FEE", "LOCKER RENT",
                 "INSTA ALERT CHG", "DEBIT CARD ISSUANCE CHG", f"AMB CHRG INCL GST {q}",
                 "CASH HANDLING CHGS", "STOP PAYMENT CHGS", "INSUFFICIENT BAL CHGS", "DP CHARGES"]
        s = self.pick(items)
        if st == "SBI" and self.chance(0.5):
            s = "TO TRANSFER-" + s
        return s

    def sp_INTEREST(self, st, dr):
        a, yy = self.acct(), self.r.randint(23, 26)
        return self.pick(["INTEREST CREDIT", f"Int.Pd:{a}:01-04-20{yy} to 30-06-20{yy}",
                          "CREDIT INTEREST CAPITALISED", "SB INTEREST", f"{a}:Int.Pd:01-07-20{yy} to 30-09-20{yy}",
                          "INT.PD", "BY INT.", f"INTEREST PAID TILL {self.r.randint(1, 28)}-{self.pick(C.MONTHS)}-20{yy}",
                          "SAVINGS INT", "FD INT CREDIT", "SWEEP INT", "CREDIT INTEREST", "INT CR",
                          "BY TRANSFER-INTEREST"])

    def sp_SELF_TRANSFER(self, st, dr):
        me, a = self.self_name(), self.acct()
        bname, code = self.bank()
        if dr:
            return self.pick(["TO SELF", f"SELF TRANSFER TO {bname}", f"FT - DR - {a} - {me}",
                              "TRANSFER TO OWN A/C", f"UPI/DR/{self.rrn()}/{me}/{code}/{me.split()[0].lower()}@{self.pick(C.PERSON_HANDLES)}/Self",
                              f"IMPS-{self.digits(12)}-{me}-{code}-XXXXXXXX{self.digits(4)}-SELF",
                              f"TRF TO {me} OWN A/C", "SELF", f"UPI/{self.digits(5)}/LOAD/LITE",
                              "UPI LITE LOAD", f"UPI LITE TOPUP {self.rrn()}", "ADD MONEY TO UPI LITE"])
        return self.pick(["BY CASH DEPOSIT", "CASH DEPOSIT", f"CDM DEP {self.digits(6)}", "BY CASH",
                          f"CASH DEP {self.pick(C.CITIES)}", "BNA/CASH DEPOSIT", f"FT - CR - {a} - {me}",
                          f"NEFT CR-{self.ifsc(code)}-{me}-{me}-{self.utr(code)}", "TRF FROM OWN A/C",
                          f"CASH-BNA-SELF-{me}", "SELF TRANSFER", f"BY SELF {me}"])

    def sp_SALARY(self, st, dr):
        m, yy, emp = self.pick(C.MONTHS), self.r.randint(23, 26), self.employer()["name"]
        return self.pick([f"SALARY FOR {m} 20{yy}", f"SAL {m}{yy} {emp}", f"{emp} SALARY",
                          f"SALARY {m}-{yy}", f"BY TRANSFER-SALARY {emp}", f"{emp} SAL CREDIT {m}",
                          f"PAYROLL {emp}", f"STIPEND {m} {yy}", f"NEFT CR SALARY {emp}"])

    def sp_EMI_LOAN(self, st, dr):
        a = self.acct()
        return self.pick([f"EMI {self.digits(8)} CHQ S{self.digits(8)} {self.ddmm()}{self.digits(6)}",
                          f"LOAN EMI {a}", f"{self.bank()[0]} LOAN RECOVERY", "EMI DEBIT", f"TO LOAN A/C {a}",
                          "LOAN INSTALLMENT", f"BY TRANSFER TO LOAN A/C {a}", f"EMI RECOVERY {a}",
                          f"PERSONAL LOAN EMI {self.pick(C.MONTHS)}", f"HOME LOAN EMI {a}"])

    def sp_CREDIT_CARD_BILL(self, st, dr):
        card = self.card()
        return self.pick([f"CC {card} AUTOPAY SI-TAD", f"IB BILLPAY DR-HDFCC0-{card}",
                          f"CREDIT CARD PAYMENT {card[-4:]}", f"BIL/INFT/{self.digits(9)}/CC PAYMENT",
                          "CARD BILL PAYMENT", f"{self.pick(['SBI CARD', 'AXIS CC', 'ICICI CC', 'HDFC CC'])} {card[-4:]} AUTODEBIT",
                          f"CC PAYMENT {card}", f"CREDIT CARD BILL {card[-4:]}"])

    def sp_INVESTMENT(self, st, dr):
        a, amc = self.acct(), self.pick(C.AMCS)
        return self.pick(["PPF DEPOSIT", f"TRF TO PPF A/C {a}", f"RD INSTALLMENT {a}", f"TRANSFER TO FD {a}",
                          "FD BOOKING", "TD CREATION", "SSY DEPOSIT", f"TO RD A/C {a}", "NPS CONTRIBUTION",
                          "APY CONTRIBUTION", f"MF SIP {amc}", f"SIP {amc} {self.digits(8)}",
                          f"{amc} PURCHASE", "SWEEP TO FD", f"AUTO SWEEP OUT {a}"])

    def sp_INVESTMENT_RETURN(self, st, dr):
        co, amc = self.pick(C.DIVIDEND_COMPANIES), self.pick(C.AMCS)
        yy = self.r.randint(23, 26)
        ach = self.ch_ach(st, {"name": f"{co} {self.pick(['DIV', 'FINAL DIV', 'INTERIM DIV', 'DIVIDEND'])}"},
                          False, "")
        return self.pick([ach, ach, f"{co} DIV {yy}", f"{co} FINAL DIVIDEND {self.digits(6)}",
                          f"{co} INTERIM DIV", f"{amc} REDEMPTION", f"{amc} REDEMPTION {self.digits(8)}",
                          "FD MATURITY PROCEEDS", "RD MATURITY", "ZERODHA BROKING PAYOUT",
                          f"NEFT CR-{self.ifsc('HDFC')}-ZERODHA BROKING LTD-{self.self_name()}-{self.utr('HDFC')}",
                          "GROWW WITHDRAWAL", f"INDIAN CLEARING CORP {amc} RED", "TD CLOSURE PROCEEDS",
                          f"{co} BUYBACK PROCEEDS", "SWEEP IN FROM FD", f"UPSTOX PAYOUT {self.digits(6)}"])

    def sp_REFUND_CASHBACK(self, st, dr):
        cat = self.pick(["SHOPPING", "SHOPPING", "FOOD_DINING", "TRAVEL", "GROCERIES", "ENTERTAINMENT",
                         "TRANSPORT", "BILLS_UTILITIES"])
        cp = self.merchant(cat)
        NAME, app = cp["name"].upper(), self.pick(C.PAY_APPS)
        upi_cr = self.ch_upi(st, cp, False, self.pick(["refund", "Refund", "REFUND", "cashback", "reversal"]))
        return self.pick([upi_cr, upi_cr, f"REV-{upi_cr}", f"UPI/REV/{self.rrn()}/{NAME}", f"REFUND {NAME}",
                          f"{NAME} REFUND {self.digits(8)}", f"CASHBACK FROM {app}", f"{app} CASHBACK",
                          f"ECOM REF/{NAME}/{self.digits(10)}", f"IRCTC REFUND {self.digits(10)}",
                          f"ME DC REFUND {self.card()} {NAME}", "REWARDS CREDIT", "CASHBACK",
                          f"REVERSAL {NAME}", f"UPI REVERSAL {self.rrn()}", "ATM DECL REVERSAL",
                          f"{NAME} CASHBACK", f"FAILED TXN REVERSAL {self.rrn()}",
                          f"UPI/{self.digits(5)}/goog-payment", "GOOGLE PAY REWARD", f"GPAY REWARD {self.rrn()}",
                          f"UPI/{self.digits(5)}/REVERSAL", f"UPI/REVERSAL/{self.rrn()}"])

    def sp_CASH_WITHDRAWAL(self, st, dr):
        return self.pick([f"CASH WDL CHQ {self.digits(6)} SELF", "CASH WITHDRAWAL BY SELF", "CASH-SELF",
                          f"CSH WDL {self.pick(C.CITIES)}", "MICRO ATM CASH WDL", "AEPS CASH WITHDRAWAL",
                          "BC CASH WDL", f"SELF CHQ {self.digits(6)}", "CASH PAID"])

    def sp_OTHER(self, st, dr):
        app = self.pick(C.PAY_APPS)
        tail = self.pick(["/UPI", "//UPI", "/Pay to", "//Payment", "/-", "-", "/Paid via", "/PAYMENT FROM PH",
                          "/NA", "/Sent from", "/UPI Intent", "/collect", "/oid", "/any"])
        truncated = f"UPI/{self.digits(self.r.randint(4, 5))}{tail}"[: self.r.randint(9, 14)]
        return self.pick([f"UPI/{app}", f"UPI/{app}", f"UPI/{self.digits(self.r.randint(2, 5))}", self.digits(7),
                          f"UPI/{app}{self.alnum(2, upper=False)}", f"UPI/{app}{self.digits(self.r.randint(1, 3))}",
                          "TRANSFER", "BY TRANSFER", "TO TRANSFER", f"IMPS/{self.digits(12)}", "MISC CREDIT",
                          "MISC DEBIT", "ADJUSTMENT", "NEFT", "UPI", f"TXN {self.digits(10)}", "IMPS",
                          f"UPI/{self.rrn()}", f"{app}", f"UPI/{app}/{self.rrn()}", truncated, truncated,
                          f"UPI/{self.digits(5)}/autopay{self.pick(['hdfcbank', 'icici', 'sbi', 'axis', 'kotak'])}",
                          "MANDATE VERIFICATION", "AUTOPAY MANDATE REGN"])

    def amount(self, cat, merchant_id=None):
        if merchant_id in FIXED_AMOUNTS:
            return self.pick(FIXED_AMOUNTS[merchant_id])
        if cat in MENUS and self.chance(0.6):
            return float(self.pick(MENUS[cat]))
        lo, hi = AMOUNTS[cat]
        v = math.exp(self.r.uniform(math.log(lo), math.log(hi)))
        step = ROUND_TO.get(cat)
        if cat in ("TRANSFER_OUT", "TRANSFER_IN", "FOOD_DINING", "SHOPPING") and self.chance(0.5):
            step = self.pick([10, 50, 100])
        if cat == "FUEL" and not self.chance(0.6):
            step = None
        if step and step > 1:
            return float(max(step, round(v / step) * step))
        return round(v, 0 if (step == 1 or self.chance(0.4)) else 2)

    def row(self, cat):
        meta = CATEGORIES[cat]
        dr = {"DEBIT": True, "CREDIT": False}.get(meta["direction"])
        if dr is None:
            dr = self.chance(0.5 if cat == "SELF_TRANSFER" else 0.6)
        st = self.wpick([(w, s) for s, w in BANK_STYLES.items()])
        channel, kind = self.wpick(RECIPES[cat])

        merchant_id = cat
        if kind == "special" and channel == "special":
            text = getattr(self, f"sp_{cat}")(st, dr)
        elif channel == "atm":
            text = self.ch_atm(st)
        else:
            cp = self.counterparty(cat, kind)
            merchant_id = cp["id"]
            if cat == "SALARY":
                note = self.pick([f"SALARY {self.pick(C.MONTHS)} {self.r.randint(23, 26)}", "SAL", "SALARY", ""])
            else:
                note = self.note_for(cat, cp)
            fn = {"upi": self.ch_upi, "neft": self.ch_neft, "imps": self.ch_imps, "ach": self.ch_ach,
                  "billpay": self.ch_billpay, "cheque": self.ch_cheque, "raw": self.ch_raw}.get(channel)
            if fn:
                text = fn(st, cp, dr, note)
            else:
                text = self.ch_card_pos(st, cp, dr, note, ecom=channel == "card_ecom",
                                        si=channel == "card_si")

        text = re.sub(r"\s+", " ", text).strip(" -/")
        if st != "SHORT" and st != "ICICI" and self.chance(0.85):
            text = text.upper()
        if self.chance(0.12) and len(text) > 45:  # passbook-style truncation
            text = text[: self.r.randint(35, 60)]

        return {
            "narration": text,
            "type": "DEBIT" if dr else "CREDIT",
            "mode": CHANNEL_MODE[channel],
            "amount": self.amount(cat, merchant_id),
            "category": cat,
            "merchant_id": merchant_id,
            "bank_style": st,
            "channel": channel,
        }

    def generate(self, n, sampling="sqrt"):
        cats = list(CATEGORIES)
        if sampling == "balanced":
            weights = [1] * len(cats)
        elif sampling == "realistic":
            weights = [CATEGORIES[c]["weight"] for c in cats]
        else:
            weights = [math.sqrt(CATEGORIES[c]["weight"]) for c in cats]
        for cat in self.r.choices(cats, weights=weights, k=n):
            yield self.row(cat)
