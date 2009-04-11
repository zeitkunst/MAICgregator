-- phpMyAdmin SQL Dump
-- version 2.11.3deb1ubuntu1.1
-- http://www.phpmyadmin.net
--
-- Host: localhost
-- Generation Time: Apr 11, 2009 at 04:14 PM
-- Server version: 5.0.51
-- PHP Version: 5.2.4-2ubuntu5.5

SET SQL_MODE="NO_AUTO_VALUE_ON_ZERO";

--
-- Database: `MAICgregator`
--

-- --------------------------------------------------------

--
-- Table structure for table `comments`
--

CREATE TABLE IF NOT EXISTS `comments` (
      `cid` int(20) NOT NULL auto_increment,
      `title` varchar(255) NOT NULL,
      `content` longtext NOT NULL,
      `datetime` datetime NOT NULL,
      `handle` varchar(255) NOT NULL,
      `pid` int(20) NOT NULL,
      PRIMARY KEY  (`cid`)
    ) ENGINE=MyISAM  DEFAULT CHARSET=latin1 AUTO_INCREMENT=7 ;

    -- --------------------------------------------------------

--
-- Table structure for table `posts`
--

CREATE TABLE IF NOT EXISTS `posts` (
      `pid` int(20) NOT NULL auto_increment,
      `title` varchar(255) NOT NULL,
      `content` longtext NOT NULL,
      `datetime` datetime NOT NULL,
      `username` varchar(255) NOT NULL,
      PRIMARY KEY  (`pid`)
    ) ENGINE=MyISAM  DEFAULT CHARSET=latin1 AUTO_INCREMENT=7 ;

    -- --------------------------------------------------------

--
-- Table structure for table `users`
--

CREATE TABLE IF NOT EXISTS `users` (
      `uid` int(5) NOT NULL auto_increment,
      `username` varchar(50) NOT NULL,
      `password` varchar(255) NOT NULL,
      `name` varchar(255) NOT NULL,
      PRIMARY KEY  (`uid`)
    ) ENGINE=MyISAM  DEFAULT CHARSET=latin1 AUTO_INCREMENT=2 ;

