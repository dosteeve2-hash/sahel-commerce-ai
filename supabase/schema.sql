-- Schéma Postgres (Supabase) — migration prévue depuis SQLite (v1)
-- Équivalent de backend/app/db.py, avec types Postgres et RLS à activer.

create table if not exists products (
    id bigint generated always as identity primary key,
    name text not null unique,
    price numeric(12,2) not null check (price >= 0),
    stock integer not null default 0 check (stock >= 0),
    created_at timestamptz not null default now()
);

create table if not exists sales (
    id bigint generated always as identity primary key,
    product_id bigint not null references products(id),
    quantity integer not null check (quantity > 0),
    total numeric(12,2) not null,
    payment_method text not null default 'cash'
        check (payment_method in ('cash', 'orange_money', 'moov_money')),
    momo_ref text,
    created_at timestamptz not null default now()
);

create table if not exists momo_transactions (
    id bigint generated always as identity primary key,
    ref text not null unique,
    amount numeric(12,2) not null,
    sender text,
    operator text check (operator in ('orange_money', 'moov_money')),
    raw_sms text not null,
    matched_sale_id bigint references sales(id),
    created_at timestamptz not null default now()
);

create index if not exists idx_sales_created_at on sales(created_at);
create index if not exists idx_momo_matched on momo_transactions(matched_sale_id);

-- TODO (multi-commerçant) : colonne merchant_id + Row Level Security
-- alter table products enable row level security; ...
