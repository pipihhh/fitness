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
  `picture` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT '/media/images/default_blog.jpg',
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
INSERT INTO `blog` VALUES (1,2,'aaa','bbb','default.jpg','2019-11-14 19:42:30',1,0),(2,2,'aaa','bbb','default.jpg','2019-11-14 19:42:36',0,0),(3,2,'aaa','bbb','default.jpg','2019-11-14 19:42:36',0,0),(4,2,'aaa','bbb','default.jpg','2019-11-14 19:42:37',0,0),(5,2,'aaa','bbb','default.jpg','2019-11-14 19:42:38',0,0),(6,2,'aaa','bbb','default.jpg','2019-11-14 19:42:38',0,0);
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
  `picture` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '/media/images/default_challenge.jpg',
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
INSERT INTO `challenge` VALUES (1,'/media/images/default.jpg','<div>aaabbbccc</div>','2019-11-09','2019-11-10','2019-11-09 11:47:14',14,0,'980b8376-ebda-48eb-a'),(2,'/media/images/default.jpg','<div>aaabbbccc</div>','2019-11-09','2019-11-10','2019-11-09 11:48:01',12,0,'86aa2740-17b3-4e47-a'),(3,'/media/images/default.jpg','<div>aaabbbccc</div>','2019-11-09','2019-11-10','2019-11-09 11:49:53',0,0,'136af9f4-603c-4f1e-a'),(4,'/media/images/default.jpg','<div>aaabbbccc</div>','2019-11-09','2019-11-10','2019-11-09 12:42:05',0,0,'b036e698-ebaf-4676-a');
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
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `comment`
--

LOCK TABLES `comment` WRITE;
/*!40000 ALTER TABLE `comment` DISABLE KEYS */;
INSERT INTO `comment` VALUES (1,'hahaha','2019-11-15 20:49:33',1,2,'agag',1),(2,'hahaha','2019-11-15 20:49:40',1,2,'agag',1),(3,'hahaha','2019-11-15 20:49:41',1,2,'agag',0),(4,'hahaha','2019-11-15 20:49:42',1,2,'agag',0),(5,'aaa','2019-11-15 20:51:44',1,2,'agag',0),(6,'bbb','2019-11-15 20:52:06',1,2,'agag',0);
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
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `course`
--

LOCK TABLES `course` WRITE;
/*!40000 ALTER TABLE `course` DISABLE KEYS */;
INSERT INTO `course` VALUES (5,1,'腹肌撕裂者','2019-11-07 17:21:07',3,30,0),(6,1,'体态瑜伽·天鹅颈','2019-12-19 17:20:37',1,90,0),(7,1,'体态瑜伽·美丽腿形','2019-12-19 21:16:26',2,110,0),(8,1,'平静身心冥想','2019-12-19 22:47:38',1,40,0);
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
  `picture` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '/media/images/default_action.jpg',
  `sequence` int(11) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=21 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `course_action`
--

LOCK TABLES `course_action` WRITE;
/*!40000 ALTER TABLE `course_action` DISABLE KEYS */;
INSERT INTO `course_action` VALUES (1,5,'这是一个非常酷的动作','aaa.jpg',1),(2,6,'呼吸练习：吸气，腹部、肋骨扩张；呼气，胸骨、肋骨向下沉降。','/media/images/bd9a9ad8448a803eb5e1e4ede2dfbfee.png',1),(3,6,'右侧颈部伸展：简易盘坐于垫上；左手于体后抓握右手手腕，头部向左侧屈找左肩；右肩远离右耳向后向下展开拉向左手；下巴微收，低头缓慢向下转动；吸气头部缓慢回正','/media/images/33e594477fb17792a7d03c5365912130.png',2),(4,6,'左侧颈部伸展：简易盘坐于垫上；右手于体后抓握左手手腕，头部向右侧屈找右肩；左肩远离左耳向后向下展开拉向右手 下巴微收，低头缓慢向下转动；吸气头部缓慢回正','/media/images/ca8094e32e85dcdc574c470a8f806cb2.png',3),(5,6,'颈部左右转动：简易盘坐于垫上，肩膀放松；呼气，水平向左转动头部至最大程度； 吸气，头部缓慢回正；呼气，水平向右转动头部至最大程度； 吸气，头部缓慢回正；下巴内收，靠近锁骨，拉伸颈部后侧及上背部；双手交叉紧贴于颈部后侧，拉长颈部，再向上看，伸展颈部前侧','/media/images/983fc95f8efd45a1a5fe80baa992d549.png',4),(6,6,'猫伸展式：跪于垫面上，双膝分开与髋同宽；脚趾回勾分担膝盖的压力，双手掌压实垫面，双手分开与肩同宽；吸气，抬头凹背，胸腔和臀部上提；呼气，腹部用力向上推，脊柱一节节向上拱起；整个背部用力向上隆起，下颌找胸骨，眼睛看向肚脐','/media/images/04ba48e1709d8e0da7fc78fac50bbab9.png',5),(7,6,'下犬式：呼气，双手推地面，臀部向上来到下犬式；双手张开用力压地面，大臂外旋，推臀部（坐骨）向上，胸腔向大腿的方向，双脚有力踩地面；保持深长的呼吸','/media/images/ede525998e0373bca1cf53ebc9653b23.png',6),(8,6,'左侧猫爬：四点支撑，双膝分开与髋同宽，双腿双臂垂直于垫面；双手掌压实垫面，双手分开与肩同宽；吸气，左腿向后蹬出，呼气，抬高左腿与地面平行；右手向前伸展，眼睛看向手指的方向','/media/images/b7ed5981c0dae9c16da7fb325c46eb74.png',7),(9,6,'右侧猫爬：四点支撑，双膝分开与髋同宽，双腿双臂垂直于地面；双手掌压实垫面，双手分开与肩同宽；吸气，右腿向后蹬出，呼气，抬高右腿与地面平行；左手向前伸展，眼睛看向手指的方向','/media/images/9a6c0cd411a192831c5646d3c599fbb1.png',8),(10,6,'半起眼镜蛇式:俯卧在垫面上；双手置于在胸部两侧；吸气大臂发力撑起身体；呼气屈手肘向内夹住身体','/media/images/76bd044390622279ae6b6e5c231ecd92.png',9),(11,7,'金刚座(脚趾回勾)：面向垫子的短边，跪在垫面上，脚趾回勾；尝试让臀部坐到脚后跟上，膝盖点地；手放在大腿面，放松肩膀','/media/images/25240fcdad11e66be7a871c553a56d85.png',1),(12,7,'金刚座(脚背放平)：慢慢抬起臀部，放平脚背，坐下来；在跪姿中静坐一会，肩膀打开，双手放在腿上，掌心朝上；双眼微闭，双膝可以微微分开些，臀部坐下','/media/images/c72d613767ffcc6cc1bfbb3ee65bce17.png',2),(13,7,'脚踝拉伸：瑜伽砖垫在右侧膝盖的下方，在这停留一会；解开瑜伽砖，放到左膝下，双肩打开，肩膀下沉','/media/images/6fe5c242af1d2fa0cd6248d3dcbea7ab.png',3),(14,7,'婴儿式：随着下一次吸气，右手和左膝落地 呼气，臀部向后坐于脚后跟上；双手自然向前伸展，额头贴地','/media/images/e9767c633059385d659ddf96a53bca50.png',4),(15,7,'左侧马鞍式：吸气，起身来到跪姿，小腿向两侧打开，膝盖并拢在一起；伸出左脚向前侧伸直，臀部压实垫面，双手掌心相对；向后弯曲手肘，打开胸腔，如果可以的话，拿开瑜伽砖，慢慢躺下来；膝盖贴实地面，微闭双眼','/media/images/6ab0a86b165370a4d22ed2ffe66aa827.png',5),(16,7,'右侧马鞍式：缓缓起身，坐直身体，解开右腿，双腿抖动下，做下反侧；弯曲左膝，左小腿肌肉拨开，臀部压实垫面，伸直右腿，挺直背部；身体慢慢后仰，弯曲手肘，在这里停留一会，慢慢平躺下来','/media/images/4b898e49f7e305652b121a36dcd32af6.png',6),(17,7,'毛毛虫式：慢慢退出体式，晃动下双腿，双手提臀肌，背部挺直；脚趾回勾，深呼吸，手臂向上，眼睛看手指；呼气时，慢慢向前折叠，双手可以放在瑜伽垫上或者是抓住脚掌','/media/images/f171414ef4a6c61d5a6dfa911995cb20.png',7),(18,7,'蝴蝶式：再次吸气，回到坐姿，接下来面向垫子的长边；脚心相对，脚后跟与会阴保持小臂的距离，调整臀部肌肉；吸气，延伸脊柱，呼气，保持脊柱直立的情况下向前弯曲；两侧膝盖向下沉，双手可以放在垫面上，放松颈部；如果可以的话，头部沉下来，将前额放在脚面上','/media/images/5cb3486e506e6aa8240762c299dfcb0f.png',8),(19,8,'呼吸练习：全身放松；保持自然顺畅的呼吸','/media/images/5d6cb008a99a4fd8bb8fb07ccbb28b56.png',1),(20,8,'简易坐：选择舒适且稳定的坐姿坐下来；将目光看向地面的某一个点，稳定的看着那个点；感受呼吸，时刻不要忘记呼吸的存在，不需要刻意去吸气和呼气；观察到呼吸的存在，与身体融合','/media/images/4e49c87c251cccdb6aa85dcf4689008c.png',2);
/*!40000 ALTER TABLE `course_action` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `file_map`
--

DROP TABLE IF EXISTS `file_map`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `file_map` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `filename` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `md5` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `file_map_filename_uindex` (`filename`),
  UNIQUE KEY `file_map_md5_uindex` (`md5`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='相同的MD5文件进行缓存';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `file_map`
--

LOCK TABLES `file_map` WRITE;
/*!40000 ALTER TABLE `file_map` DISABLE KEYS */;
/*!40000 ALTER TABLE `file_map` ENABLE KEYS */;
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
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `follow`
--

LOCK TABLES `follow` WRITE;
/*!40000 ALTER TABLE `follow` DISABLE KEYS */;
INSERT INTO `follow` VALUES (1,2,9,'2019-12-12 21:44:42'),(3,2,8,'2019-12-12 21:51:03'),(4,2,7,'2019-12-12 21:51:34');
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
  `content` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `reply`
--

LOCK TABLES `reply` WRITE;
/*!40000 ALTER TABLE `reply` DISABLE KEYS */;
INSERT INTO `reply` VALUES (1,3,'2019-12-13 09:09:47',2,'agag',0,0,'xixixi');
/*!40000 ALTER TABLE `reply` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `upper_log`
--

DROP TABLE IF EXISTS `upper_log`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `upper_log` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `blog_id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `create_time` datetime NOT NULL,
  `delete_flag` tinyint(4) NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='点赞表的记录表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `upper_log`
--

LOCK TABLES `upper_log` WRITE;
/*!40000 ALTER TABLE `upper_log` DISABLE KEYS */;
INSERT INTO `upper_log` VALUES (4,1,2,'2019-11-15 21:03:07',0);
/*!40000 ALTER TABLE `upper_log` ENABLE KEYS */;
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
) ENGINE=InnoDB AUTO_INCREMENT=10 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `user`
--

LOCK TABLES `user` WRITE;
/*!40000 ALTER TABLE `user` DISABLE KEYS */;
INSERT INTO `user` VALUES (2,'account','12d63e1c16c9096f0e6d4a191b53a2ae',255,0,'feed2a6c-255b-4bd6-8'),(4,'root','891504783465bfe2474b3f96dcbd4ac7',1,0,'cc11a851-0403-4501-b'),(5,'root1','891504783465bfe2474b3f96dcbd4ac7',1,0,'778a42ac-f8a4-4326-9'),(6,'root2','891504783465bfe2474b3f96dcbd4ac7',1,0,'3005273a-ad8c-4d84-b'),(7,'root3','891504783465bfe2474b3f96dcbd4ac7',1,0,'ed7af1fe-441c-4352-b'),(8,'root4','891504783465bfe2474b3f96dcbd4ac7',1,0,'54fc6e03-4f04-40f9-a'),(9,'pipi255','6090f915ec1cc035719bdab3f1a71a86',255,0,'1d8dad52-6f3c-4c52-b');
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
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `user_info`
--

LOCK TABLES `user_info` WRITE;
/*!40000 ALTER TABLE `user_info` DISABLE KEYS */;
INSERT INTO `user_info` VALUES (1,2,'13000999988','zenofpy@qq.com',1,'/media/images/097fc7b3d709bf306e0a8077ad1b77b1.jpg',18,'mayun','nmnmnmnm','2019-11-05 16:29:36',0),(3,4,'13088997766','867649189@qq.com',0,'/media/images/default_avatar.jpg',18,'ppp',NULL,'2019-11-07 10:26:08',0),(4,5,'13088997766',NULL,0,'/media/images/default_avatar.jpg',18,'ppp',NULL,'2019-11-07 10:26:19',0),(5,6,'13088997766',NULL,0,'/media/images/default_avatar.jpg',18,'ppp',NULL,'2019-11-07 10:26:24',0),(6,7,'13088997766',NULL,0,'/media/images/default_avatar.jpg',18,'ppp',NULL,'2019-11-07 10:26:27',0),(7,8,'13088997766',NULL,0,'/media/images/default_avatar.jpg',18,'ppp',NULL,'2019-11-07 10:26:30',0),(8,9,'13099882332',NULL,1,'/media/images/default.jpg',12,'root',NULL,'2019-12-11 21:29:07',0);
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

-- Dump completed on 2019-12-19 23:31:47
