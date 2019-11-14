-- MySQL dump 10.13  Distrib 5.7.25, for macos10.14 (x86_64)
--
-- Host: 127.0.0.1    Database: ezgym
-- ------------------------------------------------------
-- Server version	5.7.25

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `blog`
--

DROP TABLE IF EXISTS `blog`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `blog` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `content` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `title` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `picture` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `create_time` datetime NOT NULL,
  `upper` int(11) NOT NULL DEFAULT '0',
  `delete_flag` int(11) DEFAULT '0',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `blog`
--

LOCK TABLES `blog` WRITE;
/*!40000 ALTER TABLE `blog` DISABLE KEYS */;
INSERT INTO `blog` VALUES (1,2,'aaa','bbb','default.jpg','2019-11-14 19:42:30',0,0),(2,2,'aaa','bbb','default.jpg','2019-11-14 19:42:36',0,0),(3,2,'aaa','bbb','default.jpg','2019-11-14 19:42:36',0,0),(4,2,'aaa','bbb','default.jpg','2019-11-14 19:42:37',0,0),(5,2,'aaa','bbb','default.jpg','2019-11-14 19:42:38',0,0),(6,2,'aaa','bbb','default.jpg','2019-11-14 19:42:38',0,0);
/*!40000 ALTER TABLE `blog` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `challenge`
--

DROP TABLE IF EXISTS `challenge`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `challenge` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `picture` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `content` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `start_time` date NOT NULL,
  `end_time` date NOT NULL,
  `create_time` datetime NOT NULL,
  `pageviews` int(11) NOT NULL,
  `delete_flag` tinyint(4) NOT NULL DEFAULT '0',
  `number` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `challenge_number_uindex` (`number`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `challenge`
--

LOCK TABLES `challenge` WRITE;
/*!40000 ALTER TABLE `challenge` DISABLE KEYS */;
INSERT INTO `challenge` VALUES (1,'default.jpg','<div>aaabbbccc</div>','2019-11-09','2019-11-10','2019-11-09 11:47:14',0,0,'980b8376-ebda-48eb-a'),(2,'default.jpg','<div>aaabbbccc</div>','2019-11-09','2019-11-10','2019-11-09 11:48:01',0,0,'86aa2740-17b3-4e47-a'),(3,'default.jpg','<div>aaabbbccc</div>','2019-11-09','2019-11-10','2019-11-09 11:49:53',0,0,'136af9f4-603c-4f1e-a'),(4,'default.jpg','<div>aaabbbccc</div>','2019-11-09','2019-11-10','2019-11-09 12:42:05',0,0,'b036e698-ebaf-4676-a');
/*!40000 ALTER TABLE `challenge` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `collect_course`
--

DROP TABLE IF EXISTS `collect_course`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `collect_course` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `course_id` int(11) NOT NULL,
  `create_time` datetime NOT NULL,
  `delete_flag` tinyint(4) NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id` (`user_id`,`course_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `collect_course`
--

LOCK TABLES `collect_course` WRITE;
/*!40000 ALTER TABLE `collect_course` DISABLE KEYS */;
/*!40000 ALTER TABLE `collect_course` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `comment`
--

DROP TABLE IF EXISTS `comment`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `comment` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `content` varchar(1024) COLLATE utf8mb4_unicode_ci NOT NULL,
  `create_time` datetime NOT NULL,
  `blog_id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `nick_name` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `delete_flag` tinyint(4) NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `comment`
--

LOCK TABLES `comment` WRITE;
/*!40000 ALTER TABLE `comment` DISABLE KEYS */;
/*!40000 ALTER TABLE `comment` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `course`
--

DROP TABLE IF EXISTS `course`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `course` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `type` tinyint(4) NOT NULL,
  `name` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `create_time` datetime NOT NULL,
  `level` int(11) NOT NULL,
  `burning` int(11) NOT NULL,
  `delete_flag` tinyint(4) NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`),
  UNIQUE KEY `course_name_uindex` (`name`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `course`
--

LOCK TABLES `course` WRITE;
/*!40000 ALTER TABLE `course` DISABLE KEYS */;
INSERT INTO `course` VALUES (5,1,'腹肌撕裂者','2019-11-07 17:21:07',3,30,0);
/*!40000 ALTER TABLE `course` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `course_action`
--

DROP TABLE IF EXISTS `course_action`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `course_action` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `course_id` int(11) NOT NULL,
  `content` varchar(2048) COLLATE utf8mb4_unicode_ci NOT NULL,
  `picture` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `sequence` int(11) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `course_action`
--

LOCK TABLES `course_action` WRITE;
/*!40000 ALTER TABLE `course_action` DISABLE KEYS */;
INSERT INTO `course_action` VALUES (1,5,'这是一个非常酷的动作','aaa.jpg',1);
/*!40000 ALTER TABLE `course_action` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `follow`
--

DROP TABLE IF EXISTS `follow`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `follow` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `from_user` int(11) NOT NULL,
  `to_user` int(11) NOT NULL,
  `create_time` datetime NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `follow`
--

LOCK TABLES `follow` WRITE;
/*!40000 ALTER TABLE `follow` DISABLE KEYS */;
/*!40000 ALTER TABLE `follow` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `reply`
--

DROP TABLE IF EXISTS `reply`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `reply` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `comment_id` int(11) NOT NULL,
  `create_time` datetime NOT NULL,
  `user_id` int(11) NOT NULL,
  `nick_name` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `reply_id` int(11) NOT NULL,
  `delete_flag` tinyint(4) NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `reply`
--

LOCK TABLES `reply` WRITE;
/*!40000 ALTER TABLE `reply` DISABLE KEYS */;
/*!40000 ALTER TABLE `reply` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `user`
--

DROP TABLE IF EXISTS `user`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `user` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `account` varchar(18) COLLATE utf8mb4_unicode_ci NOT NULL,
  `password` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `permission` int(11) NOT NULL,
  `delete_flag` tinyint(4) NOT NULL DEFAULT '0',
  `number` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_number_uindex` (`number`)
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `user`
--

LOCK TABLES `user` WRITE;
/*!40000 ALTER TABLE `user` DISABLE KEYS */;
INSERT INTO `user` VALUES (2,'account','12d63e1c16c9096f0e6d4a191b53a2ae',255,0,'feed2a6c-255b-4bd6-8'),(4,'root','891504783465bfe2474b3f96dcbd4ac7',1,0,'cc11a851-0403-4501-b'),(5,'root1','891504783465bfe2474b3f96dcbd4ac7',1,0,'778a42ac-f8a4-4326-9'),(6,'root2','891504783465bfe2474b3f96dcbd4ac7',1,0,'3005273a-ad8c-4d84-b'),(7,'root3','891504783465bfe2474b3f96dcbd4ac7',1,0,'ed7af1fe-441c-4352-b'),(8,'root4','891504783465bfe2474b3f96dcbd4ac7',1,0,'54fc6e03-4f04-40f9-a');
/*!40000 ALTER TABLE `user` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `user_info`
--

DROP TABLE IF EXISTS `user_info`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `user_info` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `phone` varchar(11) COLLATE utf8mb4_unicode_ci NOT NULL,
  `email` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `gender` tinyint(4) NOT NULL,
  `avatar` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '/media/images/default_avatar.jpg',
  `age` int(11) NOT NULL,
  `nick_name` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL,
  `description` varchar(1024) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `create_time` datetime NOT NULL,
  `delete_flag` tinyint(4) NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id` (`user_id`)
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `user_info`
--

LOCK TABLES `user_info` WRITE;
/*!40000 ALTER TABLE `user_info` DISABLE KEYS */;
INSERT INTO `user_info` VALUES (1,2,'13000999988',NULL,1,'/index/static/default.png',18,'agag',NULL,'2019-11-05 16:29:36',0),(3,4,'13088997766',NULL,0,'/media/images/default_avatar.jpg',18,'ppp',NULL,'2019-11-07 10:26:08',0),(4,5,'13088997766',NULL,0,'/media/images/default_avatar.jpg',18,'ppp',NULL,'2019-11-07 10:26:19',0),(5,6,'13088997766',NULL,0,'/media/images/default_avatar.jpg',18,'ppp',NULL,'2019-11-07 10:26:24',0),(6,7,'13088997766',NULL,0,'/media/images/default_avatar.jpg',18,'ppp',NULL,'2019-11-07 10:26:27',0),(7,8,'13088997766',NULL,0,'/media/images/default_avatar.jpg',18,'ppp',NULL,'2019-11-07 10:26:30',0);
/*!40000 ALTER TABLE `user_info` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2019-11-14 20:08:37
