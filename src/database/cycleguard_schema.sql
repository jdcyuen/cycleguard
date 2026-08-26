--
-- PostgreSQL database dump
--

-- Dumped from database version 17.3
-- Dumped by pg_dump version 17.3

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: cycleguard; Type: SCHEMA; Schema: -; Owner: cycleguard_user
--

CREATE SCHEMA cycleguard;


ALTER SCHEMA cycleguard OWNER TO cycleguard_user;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: accounts; Type: TABLE; Schema: cycleguard; Owner: cycleguard_user
--

CREATE TABLE cycleguard.accounts (
    id integer NOT NULL,
    account_number character varying(50) NOT NULL,
    name character varying(100),
    institution character varying(50) NOT NULL,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now()
);


ALTER TABLE cycleguard.accounts OWNER TO cycleguard_user;

--
-- Name: accounts_id_seq; Type: SEQUENCE; Schema: cycleguard; Owner: cycleguard_user
--

CREATE SEQUENCE cycleguard.accounts_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE cycleguard.accounts_id_seq OWNER TO cycleguard_user;

--
-- Name: accounts_id_seq; Type: SEQUENCE OWNED BY; Schema: cycleguard; Owner: cycleguard_user
--

ALTER SEQUENCE cycleguard.accounts_id_seq OWNED BY cycleguard.accounts.id;


--
-- Name: import_history; Type: TABLE; Schema: cycleguard; Owner: cycleguard_user
--

CREATE TABLE cycleguard.import_history (
    id integer NOT NULL,
    account_id integer NOT NULL,
    import_type character varying(50) NOT NULL,
    filename character varying(255) NOT NULL,
    file_hash character varying(64) NOT NULL,
    rows_read integer DEFAULT 0 NOT NULL,
    status character varying(20) DEFAULT 'STARTED'::character varying NOT NULL,
    institution text NOT NULL,
    snapshot_date date,
    import_timestamp timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    rows_imported integer DEFAULT 0 NOT NULL,
    rows_skipped integer DEFAULT 0 NOT NULL,
    elapsed_ms integer DEFAULT 0 NOT NULL,
    error_message text
);


ALTER TABLE cycleguard.import_history OWNER TO cycleguard_user;

--
-- Name: import_history_id_seq; Type: SEQUENCE; Schema: cycleguard; Owner: cycleguard_user
--

CREATE SEQUENCE cycleguard.import_history_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE cycleguard.import_history_id_seq OWNER TO cycleguard_user;

--
-- Name: import_history_id_seq; Type: SEQUENCE OWNED BY; Schema: cycleguard; Owner: cycleguard_user
--

ALTER SEQUENCE cycleguard.import_history_id_seq OWNED BY cycleguard.import_history.id;


--
-- Name: positions; Type: TABLE; Schema: cycleguard; Owner: cycleguard_user
--

CREATE TABLE cycleguard.positions (
    id integer NOT NULL,
    account_id integer,
    security_id integer,
    snapshot_id integer,
    quantity numeric(20,6),
    avg_cost numeric(20,6),
    cost_basis_total numeric(20,2),
    current_value numeric(20,2),
    percent_of_account numeric(10,4),
    daily_gain numeric(20,2),
    daily_gain_pct numeric(10,4),
    total_gain numeric(20,2),
    total_gain_pct numeric(10,4),
    created_at timestamp without time zone DEFAULT now(),
    import_history_id integer
);


ALTER TABLE cycleguard.positions OWNER TO cycleguard_user;

--
-- Name: positions_id_seq; Type: SEQUENCE; Schema: cycleguard; Owner: cycleguard_user
--

CREATE SEQUENCE cycleguard.positions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE cycleguard.positions_id_seq OWNER TO cycleguard_user;

--
-- Name: positions_id_seq; Type: SEQUENCE OWNED BY; Schema: cycleguard; Owner: cycleguard_user
--

ALTER SEQUENCE cycleguard.positions_id_seq OWNED BY cycleguard.positions.id;


--
-- Name: securities; Type: TABLE; Schema: cycleguard; Owner: cycleguard_user
--

CREATE TABLE cycleguard.securities (
    id integer NOT NULL,
    symbol character varying(20) NOT NULL,
    description character varying(255),
    asset_type character varying(50),
    created_at timestamp without time zone DEFAULT now()
);


ALTER TABLE cycleguard.securities OWNER TO cycleguard_user;

--
-- Name: securities_id_seq; Type: SEQUENCE; Schema: cycleguard; Owner: cycleguard_user
--

CREATE SEQUENCE cycleguard.securities_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE cycleguard.securities_id_seq OWNER TO cycleguard_user;

--
-- Name: securities_id_seq; Type: SEQUENCE OWNED BY; Schema: cycleguard; Owner: cycleguard_user
--

ALTER SEQUENCE cycleguard.securities_id_seq OWNED BY cycleguard.securities.id;


--
-- Name: snapshots; Type: TABLE; Schema: cycleguard; Owner: cycleguard_user
--

CREATE TABLE cycleguard.snapshots (
    id integer NOT NULL,
    snapshot_date date NOT NULL,
    created_at timestamp without time zone DEFAULT now(),
    account_id bigint,
    import_history_id integer
);


ALTER TABLE cycleguard.snapshots OWNER TO cycleguard_user;

--
-- Name: snapshots_id_seq; Type: SEQUENCE; Schema: cycleguard; Owner: cycleguard_user
--

CREATE SEQUENCE cycleguard.snapshots_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE cycleguard.snapshots_id_seq OWNER TO cycleguard_user;

--
-- Name: snapshots_id_seq; Type: SEQUENCE OWNED BY; Schema: cycleguard; Owner: cycleguard_user
--

ALTER SEQUENCE cycleguard.snapshots_id_seq OWNED BY cycleguard.snapshots.id;


--
-- Name: transactions; Type: TABLE; Schema: cycleguard; Owner: cycleguard_user
--

CREATE TABLE cycleguard.transactions (
    id integer NOT NULL,
    account_id integer NOT NULL,
    security_id integer,
    run_date date NOT NULL,
    settlement_date date,
    action character varying(100) NOT NULL,
    trade_type character varying(100),
    price numeric(20,6),
    quantity numeric(20,6),
    commission numeric(20,2),
    fees numeric(20,2),
    accrued_interest numeric(20,2),
    amount numeric(20,2) NOT NULL,
    cash_balance numeric(20,2),
    created_at timestamp without time zone DEFAULT now(),
    import_history_id integer
);


ALTER TABLE cycleguard.transactions OWNER TO cycleguard_user;

--
-- Name: transactions_id_seq; Type: SEQUENCE; Schema: cycleguard; Owner: cycleguard_user
--

CREATE SEQUENCE cycleguard.transactions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE cycleguard.transactions_id_seq OWNER TO cycleguard_user;

--
-- Name: transactions_id_seq; Type: SEQUENCE OWNED BY; Schema: cycleguard; Owner: cycleguard_user
--

ALTER SEQUENCE cycleguard.transactions_id_seq OWNED BY cycleguard.transactions.id;


--
-- Name: accounts id; Type: DEFAULT; Schema: cycleguard; Owner: cycleguard_user
--

ALTER TABLE ONLY cycleguard.accounts ALTER COLUMN id SET DEFAULT nextval('cycleguard.accounts_id_seq'::regclass);


--
-- Name: import_history id; Type: DEFAULT; Schema: cycleguard; Owner: cycleguard_user
--

ALTER TABLE ONLY cycleguard.import_history ALTER COLUMN id SET DEFAULT nextval('cycleguard.import_history_id_seq'::regclass);


--
-- Name: positions id; Type: DEFAULT; Schema: cycleguard; Owner: cycleguard_user
--

ALTER TABLE ONLY cycleguard.positions ALTER COLUMN id SET DEFAULT nextval('cycleguard.positions_id_seq'::regclass);


--
-- Name: securities id; Type: DEFAULT; Schema: cycleguard; Owner: cycleguard_user
--

ALTER TABLE ONLY cycleguard.securities ALTER COLUMN id SET DEFAULT nextval('cycleguard.securities_id_seq'::regclass);


--
-- Name: snapshots id; Type: DEFAULT; Schema: cycleguard; Owner: cycleguard_user
--

ALTER TABLE ONLY cycleguard.snapshots ALTER COLUMN id SET DEFAULT nextval('cycleguard.snapshots_id_seq'::regclass);


--
-- Name: transactions id; Type: DEFAULT; Schema: cycleguard; Owner: cycleguard_user
--

ALTER TABLE ONLY cycleguard.transactions ALTER COLUMN id SET DEFAULT nextval('cycleguard.transactions_id_seq'::regclass);


--
-- Name: accounts accounts_pkey; Type: CONSTRAINT; Schema: cycleguard; Owner: cycleguard_user
--

ALTER TABLE ONLY cycleguard.accounts
    ADD CONSTRAINT accounts_pkey PRIMARY KEY (id);


--
-- Name: import_history import_history_pkey; Type: CONSTRAINT; Schema: cycleguard; Owner: cycleguard_user
--

ALTER TABLE ONLY cycleguard.import_history
    ADD CONSTRAINT import_history_pkey PRIMARY KEY (id);


--
-- Name: positions positions_pkey; Type: CONSTRAINT; Schema: cycleguard; Owner: cycleguard_user
--

ALTER TABLE ONLY cycleguard.positions
    ADD CONSTRAINT positions_pkey PRIMARY KEY (id);


--
-- Name: securities securities_pkey; Type: CONSTRAINT; Schema: cycleguard; Owner: cycleguard_user
--

ALTER TABLE ONLY cycleguard.securities
    ADD CONSTRAINT securities_pkey PRIMARY KEY (id);


--
-- Name: securities securities_ticker_key; Type: CONSTRAINT; Schema: cycleguard; Owner: cycleguard_user
--

ALTER TABLE ONLY cycleguard.securities
    ADD CONSTRAINT securities_ticker_key UNIQUE (symbol);


--
-- Name: snapshots snapshots_pkey; Type: CONSTRAINT; Schema: cycleguard; Owner: cycleguard_user
--

ALTER TABLE ONLY cycleguard.snapshots
    ADD CONSTRAINT snapshots_pkey PRIMARY KEY (id);


--
-- Name: transactions transactions_pkey; Type: CONSTRAINT; Schema: cycleguard; Owner: cycleguard_user
--

ALTER TABLE ONLY cycleguard.transactions
    ADD CONSTRAINT transactions_pkey PRIMARY KEY (id);


--
-- Name: import_history uq_import_history; Type: CONSTRAINT; Schema: cycleguard; Owner: cycleguard_user
--

ALTER TABLE ONLY cycleguard.import_history
    ADD CONSTRAINT uq_import_history UNIQUE (account_id, import_type, file_hash);


--
-- Name: snapshots uq_snapshot; Type: CONSTRAINT; Schema: cycleguard; Owner: cycleguard_user
--

ALTER TABLE ONLY cycleguard.snapshots
    ADD CONSTRAINT uq_snapshot UNIQUE (id, snapshot_date);


--
-- Name: transactions uq_transaction; Type: CONSTRAINT; Schema: cycleguard; Owner: cycleguard_user
--

ALTER TABLE ONLY cycleguard.transactions
    ADD CONSTRAINT uq_transaction UNIQUE (account_id, run_date, security_id, amount, action, trade_type);


--
-- Name: positions fk_positions_account; Type: FK CONSTRAINT; Schema: cycleguard; Owner: cycleguard_user
--

ALTER TABLE ONLY cycleguard.positions
    ADD CONSTRAINT fk_positions_account FOREIGN KEY (account_id) REFERENCES cycleguard.accounts(id);


--
-- Name: positions fk_positions_import_history; Type: FK CONSTRAINT; Schema: cycleguard; Owner: cycleguard_user
--

ALTER TABLE ONLY cycleguard.positions
    ADD CONSTRAINT fk_positions_import_history FOREIGN KEY (import_history_id) REFERENCES cycleguard.import_history(id);


--
-- Name: positions fk_positions_security; Type: FK CONSTRAINT; Schema: cycleguard; Owner: cycleguard_user
--

ALTER TABLE ONLY cycleguard.positions
    ADD CONSTRAINT fk_positions_security FOREIGN KEY (security_id) REFERENCES cycleguard.securities(id);


--
-- Name: positions fk_positions_snapshot; Type: FK CONSTRAINT; Schema: cycleguard; Owner: cycleguard_user
--

ALTER TABLE ONLY cycleguard.positions
    ADD CONSTRAINT fk_positions_snapshot FOREIGN KEY (snapshot_id) REFERENCES cycleguard.snapshots(id);


--
-- Name: snapshots fk_snapshots_import_history; Type: FK CONSTRAINT; Schema: cycleguard; Owner: cycleguard_user
--

ALTER TABLE ONLY cycleguard.snapshots
    ADD CONSTRAINT fk_snapshots_import_history FOREIGN KEY (import_history_id) REFERENCES cycleguard.import_history(id);


--
-- Name: transactions fk_transactions_import_history; Type: FK CONSTRAINT; Schema: cycleguard; Owner: cycleguard_user
--

ALTER TABLE ONLY cycleguard.transactions
    ADD CONSTRAINT fk_transactions_import_history FOREIGN KEY (import_history_id) REFERENCES cycleguard.import_history(id);


--
-- Name: import_history import_history_account_id_fkey; Type: FK CONSTRAINT; Schema: cycleguard; Owner: cycleguard_user
--

ALTER TABLE ONLY cycleguard.import_history
    ADD CONSTRAINT import_history_account_id_fkey FOREIGN KEY (account_id) REFERENCES cycleguard.accounts(id);


--
-- Name: snapshots snapshots_account_id_fkey; Type: FK CONSTRAINT; Schema: cycleguard; Owner: cycleguard_user
--

ALTER TABLE ONLY cycleguard.snapshots
    ADD CONSTRAINT snapshots_account_id_fkey FOREIGN KEY (account_id) REFERENCES cycleguard.accounts(id);


--
-- Name: transactions transactions_account_id_fkey; Type: FK CONSTRAINT; Schema: cycleguard; Owner: cycleguard_user
--

ALTER TABLE ONLY cycleguard.transactions
    ADD CONSTRAINT transactions_account_id_fkey FOREIGN KEY (account_id) REFERENCES cycleguard.accounts(id);


--
-- Name: transactions transactions_security_id_fkey; Type: FK CONSTRAINT; Schema: cycleguard; Owner: cycleguard_user
--

ALTER TABLE ONLY cycleguard.transactions
    ADD CONSTRAINT transactions_security_id_fkey FOREIGN KEY (security_id) REFERENCES cycleguard.securities(id);


--
-- PostgreSQL database dump complete
--

