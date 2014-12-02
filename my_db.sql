DROP TABLE IF EXISTS users;
CREATE TABLE users (
  id          INT AUTO_INCREMENT  NOT NULL,
  username    VARCHAR(255),
  name        VARCHAR(255),
  about       TEXT,
  isAnonymous BOOL DEFAULT FALSE  NOT NULL,
  email       VARCHAR(255) UNIQUE NOT NULL,
  PRIMARY KEY (id),
  KEY email_id (email, id)
);

DROP TABLE IF EXISTS follower_followee;
CREATE TABLE follower_followee (
  follower INT NOT NULL,
  followee INT NOT NULL,
  PRIMARY KEY (follower, followee),
  KEY f_f (followee, follower)
);

DROP TABLE IF EXISTS forums;
CREATE TABLE forums (
  id         INT AUTO_INCREMENT NOT NULL,
  name       VARCHAR(255)       NOT NULL UNIQUE,
  short_name VARCHAR(255)       NOT NULL UNIQUE,
  user       VARCHAR(255)       NOT NULL,
  PRIMARY KEY (id),
  KEY (short_name)
);

DROP TABLE IF EXISTS threads;
CREATE TABLE threads (
  id        INT AUTO_INCREMENT NOT NULL,
  posts     INT DEFAULT 0      NOT NULL,
  likes     INT DEFAULT 0      NOT NULL,
  dislikes  INT DEFAULT 0      NOT NULL,
  points    INT DEFAULT 0      NOT NULL,
  isDeleted BOOL DEFAULT FALSE NOT NULL,
  isClosed  BOOL DEFAULT FALSE NOT NULL,
  forum     VARCHAR(255)       NOT NULL,
  title     VARCHAR(255)       NOT NULL,
  user      VARCHAR(255)       NOT NULL,
  date      DATETIME           NOT NULL,
  message   TEXT               NOT NULL,
  slug      VARCHAR(255)       NOT NULL,
  PRIMARY KEY (id),
  KEY (forum)
);

DROP TABLE IF EXISTS posts;
CREATE TABLE posts (
  id            INT AUTO_INCREMENT NOT NULL,
  parent        INT DEFAULT NULL,
  thread        INT                NOT NULL,
  likes         INT DEFAULT 0      NOT NULL,
  dislikes      INT DEFAULT 0      NOT NULL,
  points        INT DEFAULT 0      NOT NULL,
  isDeleted     BOOL DEFAULT FALSE NOT NULL,
  isSpam        BOOL DEFAULT FALSE NOT NULL,
  isEdited      BOOL DEFAULT FALSE NOT NULL,
  isApproved    BOOL DEFAULT FALSE NOT NULL,
  isHighlighted BOOL DEFAULT FALSE NOT NULL,
  forum         VARCHAR(255)       NOT NULL,
  user          VARCHAR(255)       NOT NULL,
  date          DATETIME           NOT NULL,
  message       TEXT               NOT NULL,
  PRIMARY KEY (id),
  KEY (user),
  KEY (forum)
);

DROP TABLE IF EXISTS users_threads;
CREATE TABLE users_threads (
  user   VARCHAR(255) NOT NULL,
  thread INT          NOT NULL,
  PRIMARY KEY (user, thread)
);