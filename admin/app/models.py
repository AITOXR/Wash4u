"""SQLAlchemy models for the control plane.

Everything here lives in Postgres (or SQLite locally) — never in the git
repo. content/ (the git repo) only ever receives what Publish serialises
into it. See app/publish.py.
"""
from __future__ import annotations

import enum

from sqlalchemy import (
    Boolean, Column, DateTime, Enum, ForeignKey, Integer, JSON, String, Text,
    UniqueConstraint, func,
)
from sqlalchemy.orm import relationship

from app.db import Base


class Role(str, enum.Enum):
    owner = "owner"
    editor = "editor"
    staff = "staff"


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    role = Column(Enum(Role), nullable=False, default=Role.editor)
    must_change_password = Column(Boolean, default=False, nullable=False)
    totp_secret = Column(String, nullable=True)  # set once 2FA is turned on
    totp_enabled = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")


class Session(Base):
    """Server-side session store — the cookie only carries a signed session id."""
    __tablename__ = "sessions"
    id = Column(String, primary_key=True)  # random token
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
    user_agent = Column(String, nullable=True)
    ip = Column(String, nullable=True)

    user = relationship("User", back_populates="sessions")


class LoginAttempt(Base):
    """Rolling log of login attempts, for the 5-strikes/15-minute lockout."""
    __tablename__ = "login_attempts"
    id = Column(Integer, primary_key=True)
    email = Column(String, index=True, nullable=False)
    ip = Column(String, index=True, nullable=False)
    success = Column(Boolean, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class PageStatus(str, enum.Enum):
    draft = "draft"
    published = "published"


class Page(Base):
    __tablename__ = "pages"
    id = Column(Integer, primary_key=True)
    slug = Column(String, unique=True, nullable=False, index=True)  # "" for homepage
    title = Column(String, nullable=False)
    seo_title = Column(String, nullable=True)
    seo_description = Column(Text, nullable=True)
    canonical = Column(String, nullable=True)
    og_title = Column(String, nullable=True)
    og_description = Column(Text, nullable=True)
    og_image = Column(String, nullable=True)
    status = Column(Enum(PageStatus), default=PageStatus.draft, nullable=False)
    is_home = Column(Boolean, default=False, nullable=False)
    depth = Column(Integer, default=1, nullable=False)
    order = Column(Integer, default=0, nullable=False)
    # Draft/live split (Phase: Draft vs Live): `sections` on this row is
    # always the DRAFT state. `published_snapshot` is the JSON blob of
    # sections as they looked at the last publish, used for "revert to
    # last published" without touching the revisions table.
    published_snapshot = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    sections = relationship("Section", back_populates="page", cascade="all, delete-orphan", order_by="Section.order")


class Section(Base):
    __tablename__ = "sections"
    id = Column(Integer, primary_key=True)
    page_id = Column(Integer, ForeignKey("pages.id"), nullable=False)
    type = Column(String, nullable=False)  # matches a schemas/sections/<type>.yml
    order = Column(Integer, default=0, nullable=False)
    is_visible = Column(Boolean, default=True, nullable=False)
    hide_on_mobile = Column(Boolean, default=False, nullable=False)
    props = Column(JSON, default=dict, nullable=False)
    style = Column(JSON, default=dict, nullable=False)  # background, padding, alignment, max width

    page = relationship("Page", back_populates="sections")


class SectionPreset(Base):
    """A section saved as a reusable preset — 'Templates' in the spec."""
    __tablename__ = "section_presets"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)
    props = Column(JSON, default=dict, nullable=False)
    style = Column(JSON, default=dict, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    slug = Column(String, unique=True, nullable=False)
    parent_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    image = Column(String, nullable=True)
    order = Column(Integer, default=0, nullable=False)
    seo_title = Column(String, nullable=True)
    seo_description = Column(Text, nullable=True)


class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True)
    slug = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    short_desc = Column(Text, nullable=True)
    long_desc = Column(Text, nullable=True)  # Markdown
    price = Column(String, nullable=True)  # kept as display text ("₹149") — matches src data
    sale_price = Column(String, nullable=True)
    currency = Column(String, default="INR", nullable=False)
    unit_label = Column(String, nullable=True)  # "per kg", "per piece"
    images = Column(JSON, default=list, nullable=False)  # ["images/...", ...], first = primary
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    tags = Column(JSON, default=list, nullable=False)
    stock_tracked = Column(Boolean, default=False, nullable=False)
    stock_qty = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    order = Column(Integer, default=0, nullable=False)
    seo_title = Column(String, nullable=True)
    seo_description = Column(Text, nullable=True)
    custom_fields = Column(JSON, default=dict, nullable=False)
    status = Column(Enum(PageStatus), default=PageStatus.published, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class ProductVariant(Base):
    __tablename__ = "product_variants"
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    name = Column(String, nullable=False)  # e.g. "Large", "Premium tier"
    price = Column(String, nullable=False)
    stock_qty = Column(Integer, nullable=True)


class BlogPost(Base):
    __tablename__ = "blog_posts"
    id = Column(Integer, primary_key=True)
    slug = Column(String, unique=True, nullable=False, index=True)
    title = Column(String, nullable=False)
    excerpt = Column(Text, nullable=True)
    body = Column(Text, nullable=True)  # Markdown
    cover_image = Column(String, nullable=True)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    tags = Column(JSON, default=list, nullable=False)
    status = Column(String, default="draft", nullable=False)  # draft | scheduled | published
    published_at = Column(DateTime(timezone=True), nullable=True)
    seo_title = Column(String, nullable=True)
    seo_description = Column(Text, nullable=True)
    canonical = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Media(Base):
    __tablename__ = "media"
    id = Column(Integer, primary_key=True)
    filename = Column(String, nullable=False)
    url = Column(String, nullable=False)  # path under content/media/ once published
    alt = Column(String, nullable=True)
    caption = Column(String, nullable=True)
    folder = Column(String, nullable=True)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    size_bytes = Column(Integer, nullable=True)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())


class LeadStatus(str, enum.Enum):
    new = "new"
    contacted = "contacted"
    quoted = "quoted"
    won = "won"
    lost = "lost"


class Lead(Base):
    __tablename__ = "leads"
    id = Column(Integer, primary_key=True)
    source = Column(String, nullable=False)  # "contact_form", "callback", etc.
    name = Column(String, nullable=True)
    phone = Column(String, nullable=True, index=True)
    email = Column(String, nullable=True)
    payload = Column(JSON, default=dict, nullable=False)
    status = Column(Enum(LeadStatus), default=LeadStatus.new, nullable=False)
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=True)
    notes = Column(Text, nullable=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class OrderStatus(str, enum.Enum):
    new = "new"
    confirmed = "confirmed"
    in_progress = "in_progress"
    ready = "ready"
    out_for_delivery = "out_for_delivery"
    completed = "completed"
    cancelled = "cancelled"
    refunded = "refunded"


class Order(Base):
    """A booking/enquiry record, NOT a paid transaction — see the decision
    recorded in docs/decisions or the phase-1 chat summary: this site takes
    real bookings via WhatsApp + an external booking app, so "orders" here
    are enquiry/booking records staff track manually, not a payment flow."""
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True)
    customer_name = Column(String, nullable=True)
    customer_phone = Column(String, nullable=True, index=True)
    customer_email = Column(String, nullable=True)
    address = Column(Text, nullable=True)
    slot = Column(String, nullable=True)  # requested pickup date/time, free text
    status = Column(Enum(OrderStatus), default=OrderStatus.new, nullable=False)
    items = Column(JSON, default=list, nullable=False)  # [{name, qty, price}]
    subtotal = Column(String, nullable=True)
    discount = Column(String, nullable=True)
    tax = Column(String, nullable=True)
    delivery = Column(String, nullable=True)
    total = Column(String, nullable=True)
    payment_method = Column(String, nullable=True)  # cash / UPI / card — informational only
    internal_notes = Column(Text, nullable=True)
    source = Column(String, default="manual", nullable=False)  # "website", "manual", "whatsapp"
    # Guards on_order_completed() so it can never double-count LTV, no
    # matter how many times it's called for this order (a re-fired
    # webhook, a manual re-save, or a status bounced back and forward) —
    # required by spec: "must not double-count LTV".
    counted_for_crm = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class OrderStatusLog(Base):
    __tablename__ = "order_status_log"
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    from_status = Column(String, nullable=True)
    to_status = Column(String, nullable=False)
    changed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Customer(Base):
    __tablename__ = "customers"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=True)
    phone = Column(String, unique=True, nullable=True, index=True)
    email = Column(String, nullable=True, index=True)
    addresses = Column(JSON, default=list, nullable=False)
    source = Column(String, nullable=True)
    tags = Column(JSON, default=list, nullable=False)
    notes = Column(Text, nullable=True)
    total_orders = Column(Integer, default=0, nullable=False)
    lifetime_value = Column(Integer, default=0, nullable=False)  # paise/rupees as int for simple arithmetic
    avg_order_value = Column(Integer, default=0, nullable=False)
    first_order_at = Column(DateTime(timezone=True), nullable=True)
    last_order_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class CustomerTimelineEvent(Base):
    __tablename__ = "customer_timeline"
    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    kind = Column(String, nullable=False)  # order, status_change, note, call, email, form_submission
    detail = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class CustomerTask(Base):
    __tablename__ = "customer_tasks"
    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    title = Column(String, nullable=False)
    due_at = Column(DateTime(timezone=True), nullable=True)
    done = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Segment(Base):
    """A saved CRM filter — 'segment builder' in the spec."""
    __tablename__ = "segments"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    filters = Column(JSON, default=dict, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Revision(Base):
    __tablename__ = "revisions"
    id = Column(Integer, primary_key=True)
    entity_type = Column(String, nullable=False)  # "page", "product", "post", ...
    entity_id = Column(Integer, nullable=False)
    snapshot = Column(JSON, nullable=False)
    label = Column(String, nullable=True)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class AuditLog(Base):
    __tablename__ = "audit_log"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String, nullable=False)  # "update", "delete", "publish", "login", ...
    entity = Column(String, nullable=True)
    entity_id = Column(Integer, nullable=True)
    diff = Column(JSON, nullable=True)
    ip = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class NavItem(Base):
    __tablename__ = "nav_items"
    id = Column(Integer, primary_key=True)
    label = Column(String, nullable=False)
    href = Column(String, nullable=False)
    parent_id = Column(Integer, ForeignKey("nav_items.id"), nullable=True)
    order = Column(Integer, default=0, nullable=False)
    location = Column(String, nullable=False)  # "header" | "footer"


class Redirect(Base):
    __tablename__ = "redirects"
    id = Column(Integer, primary_key=True)
    __table_args__ = (UniqueConstraint("from_path", name="uq_redirect_from_path"),)
    from_path = Column(String, nullable=False)
    to_path = Column(String, nullable=False)
    status_code = Column(Integer, default=301, nullable=False)


class SiteSetting(Base):
    """Single-row-per-key settings store (branding, business info, SEO
    defaults, integrations, notifications, popups, maintenance mode).
    Simple key/JSON-value rather than one giant fixed-schema row, so
    adding a new setting never needs a migration."""
    __tablename__ = "site_settings"
    key = Column(String, primary_key=True)
    value = Column(JSON, nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class PublishLog(Base):
    __tablename__ = "publish_log"
    id = Column(Integer, primary_key=True)
    summary = Column(Text, nullable=False)  # human-readable "Home: 3 sections edited, ..."
    commit_sha = Column(String, nullable=True)
    status = Column(String, default="pending", nullable=False)  # pending|committed|building|deployed|failed
    author_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
