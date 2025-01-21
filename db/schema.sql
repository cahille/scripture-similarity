SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: vector; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS vector WITH SCHEMA public;


--
-- Name: EXTENSION vector; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION vector IS 'vector data type and ivfflat and hnsw access methods';


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: schema_migrations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.schema_migrations (
    version character varying(128) NOT NULL
);


--
-- Name: similar_verse; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.similar_verse (
    base_verse_id integer NOT NULL,
    similar_verse_id integer NOT NULL,
    score double precision NOT NULL
);


--
-- Name: verse; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.verse (
    id integer NOT NULL,
    volume character varying(100) NOT NULL,
    book character varying(100) NOT NULL,
    chapter integer NOT NULL,
    verse integer NOT NULL,
    text text NOT NULL,
    clean_text text NOT NULL,
    embedding public.vector(768) NOT NULL
);


--
-- Name: verse_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.verse_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: verse_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.verse_id_seq OWNED BY public.verse.id;


--
-- Name: verse id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.verse ALTER COLUMN id SET DEFAULT nextval('public.verse_id_seq'::regclass);


--
-- Name: schema_migrations schema_migrations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.schema_migrations
    ADD CONSTRAINT schema_migrations_pkey PRIMARY KEY (version);


--
-- Name: similar_verse similar_verse_base_verse_id_similar_verse_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.similar_verse
    ADD CONSTRAINT similar_verse_base_verse_id_similar_verse_id_key UNIQUE (base_verse_id, similar_verse_id);


--
-- Name: verse verse_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.verse
    ADD CONSTRAINT verse_pkey PRIMARY KEY (id);


--
-- Name: verse verse_volume_book_chapter_verse_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.verse
    ADD CONSTRAINT verse_volume_book_chapter_verse_key UNIQUE (volume, book, chapter, verse);


--
-- Name: similar_verse similar_verse_base_verse_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.similar_verse
    ADD CONSTRAINT similar_verse_base_verse_id_fkey FOREIGN KEY (base_verse_id) REFERENCES public.verse(id);


--
-- Name: similar_verse similar_verse_similar_verse_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.similar_verse
    ADD CONSTRAINT similar_verse_similar_verse_id_fkey FOREIGN KEY (similar_verse_id) REFERENCES public.verse(id);


--
-- PostgreSQL database dump complete
--


--
-- Dbmate schema migrations
--

INSERT INTO public.schema_migrations (version) VALUES
    ('20241023035438'),
    ('20241107062954');
