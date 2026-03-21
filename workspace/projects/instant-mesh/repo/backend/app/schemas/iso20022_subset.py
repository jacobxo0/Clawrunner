"""ISO 20022 message subset mappings for SCT Inst processing.

We ingest three key message types:
- pacs.008 (FIToFICustomerCreditTransfer) – the payment itself
- camt.056 (FIToFIPaymentCancellationRequest) – recall/cancellation
- acmt.023 (IdentificationModificationAdvice) – account identity updates

Each model captures the fields we extract for scoring; the full XML
envelope is stored as-is in the audit log.
"""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class Pacs008Extract(BaseModel):
    """Key fields from pacs.008 – credit transfer instruction."""

    msg_id: str = Field(description="GrpHdr/MsgId – unique message identifier")
    creation_dt: datetime = Field(description="GrpHdr/CreDtTm")
    nb_of_txs: int = Field(description="GrpHdr/NbOfTxs", default=1)
    settlement_method: str = Field(description="GrpHdr/SttlmInf/SttlmMtd (CLRG|INDA|INGA)")
    # Debtor
    debtor_name: str
    debtor_iban: str
    debtor_bic: str | None = None
    debtor_country: str | None = None
    # Creditor
    creditor_name: str
    creditor_iban: str
    creditor_bic: str | None = None
    creditor_country: str | None = None
    # Amount
    instructed_amount: Decimal
    currency: str = "EUR"
    # Purpose / remittance
    purpose_code: str | None = None
    remittance_info: str | None = None
    # End-to-end & UETR
    end_to_end_id: str
    uetr: str | None = Field(default=None, description="Unique end-to-end transaction reference (UUID)")


class Camt056Extract(BaseModel):
    """Key fields from camt.056 – cancellation/recall request."""

    msg_id: str
    creation_dt: datetime
    original_msg_id: str = Field(description="References the pacs.008 MsgId being recalled")
    original_end_to_end_id: str
    cancellation_reason_code: str | None = None
    cancellation_reason_info: str | None = None
    instructed_amount: Decimal
    currency: str = "EUR"


class Acmt023Extract(BaseModel):
    """Key fields from acmt.023 – identification modification advice."""

    msg_id: str
    creation_dt: datetime
    account_iban: str
    original_party_name: str | None = None
    updated_party_name: str | None = None
    modification_reason: str | None = None
