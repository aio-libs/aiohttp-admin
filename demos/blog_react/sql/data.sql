SET ROLE 'admindemo_user';

BEGIN;
-- Table: post

-- DROP TABLE post;

CREATE TABLE post
(
  "id" serial NOT NULL PRIMARY KEY,
  title character varying(200) NOT NULL,
  teaser character varying(200) NOT NULL,
  body text NOT NULL,
  views integer NOT NULL,
  average_note double precision NOT NULL,
  pictures json NOT NULL DEFAULT '{}'::json,
  tags integer[] NOT NULL DEFAULT '{}'::integer[],
  published_at date NOT NULL,
  category character varying(50) NOT NULL,
  subcategory character varying(50) NOT NULL,
  backlinks json NOT NULL DEFAULT '{}'::json
);


-- Table: tag

-- DROP TABLE tag;

CREATE TABLE tag
(
  "id" serial NOT NULL PRIMARY KEY,
  name character varying(10) NOT NULL,
  published boolean NOT NULL DEFAULT false
);

-- Table: comment

-- DROP TABLE comment;

CREATE TABLE comment
(
  "id" serial NOT NULL PRIMARY KEY,
  post_id integer NOT NULL,
  body text NOT NULL,
  created_at date NOT NULL,
  author json NOT NULL DEFAULT '{}'::json
);


COMMIT;
