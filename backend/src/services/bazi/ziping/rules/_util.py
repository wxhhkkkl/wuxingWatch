"""规则模块共用的小工具：把书中的一条条件写成 `Condition`。"""

from __future__ import annotations

from . import Citation, Condition


def c(cid: str, text: str, predicate: str, citation: Citation, *,
      status: str = "active", **params) -> Condition:
    return Condition(cid, text, "custom", predicate, citation,
                     params=params, status=status)


def has(tg: str, citation: Citation, cid: str, text: str,
        *, min_: int = 1, status: str = "active") -> Condition:
    return c(cid, text, "has_ten_god", citation, status=status,
             ten_god=tg, min=min_)


def has_any(tgs: tuple[str, ...], citation: Citation, cid: str,
            text: str, *, status: str = "active") -> Condition:
    return c(cid, text, "has_any_ten_god", citation, status=status,
             ten_gods=tgs)


def no_tou(tg: str, citation: Citation, cid: str, text: str) -> Condition:
    return c(cid, text, "no_tou_gan", citation, ten_god=tg)


def no_bad(citation: Citation, cid: str, text: str) -> Condition:
    return c(cid, text, "no_bad_relation_to_month", citation)


def open_(cid: str, text: str, citation: Citation) -> Condition:
    return c(cid, text, "always", citation, status="open")


def month_tg_in(tgs: tuple[str, ...], citation: Citation, cid: str,
                text: str) -> Condition:
    return c(cid, text, "month_ten_god_in", citation, ten_gods=tgs)


def dm_wx(wx: str, citation: Citation, cid: str, text: str) -> Condition:
    return c(cid, text, "day_master_wx", citation, wx=wx)


def dm_gan(gans: tuple[str, ...], citation: Citation, cid: str,
           text: str) -> Condition:
    return c(cid, text, "day_master_gan", citation, gan=gans)


def dm_in_relation(citation: Citation, cid: str, text: str,
                   types: tuple[str, ...] = ("五合", "天合地合")) -> Condition:
    return c(cid, text, "dm_in_relation", citation, types=types)


def yang_ren(citation: Citation, cid: str, text: str) -> Condition:
    return c(cid, text, "yang_ren", citation)


def no_ten_god(tg: str, citation: Citation, cid: str, text: str) -> Condition:
    return c(cid, text, "no_ten_god", citation, ten_god=tg)


def not_yang_ren(citation: Citation, cid: str, text: str) -> Condition:
    return c(cid, text, "not_yang_ren", citation)
