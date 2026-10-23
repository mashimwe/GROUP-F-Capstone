"""
ServiceFlow — Active case (session) state
===========================================
Week 1, User Stories 5 and 8: when the agent asks a clarifying question, the
customer's reply must CONTINUE the same case instead of starting from scratch.

This is SESSION state, deliberately separate from persistent memory (memory_store.py):
  * lives only in the running process, for one customer's open case;
  * holds the customer's own messages for that case so the next turn can be read in context;
  * is discarded as soon as the case reaches any outcome other than "waiting for the customer";
  * is bound to one verified customer id and resets if a different customer uses it.
"""

from dataclasses import dataclass, field
from typing import Optional

MAX_CASE_CHARS = 1000  # same cap as a single input message


@dataclass
class CaseSession:
    customer_id: Optional[str] = None
    turns: list = field(default_factory=list)
    awaiting_clarification: bool = False
    rounds: int = 0            # how many clarifying questions this case has already received

    def bind(self, customer_id: Optional[str]) -> None:
        """A session never carries text from one customer to another."""
        if customer_id != self.customer_id:
            self.customer_id = customer_id
            self.turns, self.awaiting_clarification, self.rounds = [], False, 0

    def effective_message(self, new_message: str) -> str:
        if self.awaiting_clarification and self.turns:
            return " ".join(self.turns + [new_message])[-MAX_CASE_CHARS:]
        return new_message

    def update(self, message: str, stop_reason: Optional[str]) -> None:
        if self.awaiting_clarification:
            self.turns.append(message)
        else:
            self.turns = [message]
        self.awaiting_clarification = stop_reason == "stop_waiting_for_customer"
        if self.awaiting_clarification:
            self.rounds += 1
        else:
            self.turns, self.rounds = [], 0  # case closed: discard the session text
