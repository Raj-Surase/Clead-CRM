-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Jul 17, 2025 at 12:07 PM
-- Server version: 10.4.32-MariaDB
-- PHP Version: 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `calendar_db`
--

-- --------------------------------------------------------

--
-- Table structure for table `calendars`
--

CREATE TABLE `calendars` (
  `id` int(11) NOT NULL,
  `name` varchar(255) NOT NULL,
  `description` text DEFAULT NULL,
  `color` varchar(7) DEFAULT NULL,
  `timezone` varchar(50) DEFAULT NULL,
  `is_default` tinyint(1) DEFAULT NULL,
  `is_public` tinyint(1) DEFAULT NULL,
  `owner_id` varchar(255) NOT NULL,
  `owner_name` varchar(255) DEFAULT NULL,
  `owner_email` varchar(255) DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `events`
--

CREATE TABLE `events` (
  `id` int(11) NOT NULL,
  `title` varchar(255) NOT NULL,
  `description` text DEFAULT NULL,
  `start_datetime` datetime NOT NULL,
  `end_datetime` datetime NOT NULL,
  `timezone` varchar(50) DEFAULT NULL,
  `all_day` tinyint(1) DEFAULT NULL,
  `event_type` enum('MEETING','CALL','APPOINTMENT','FOLLOW_UP','DEMO','PRESENTATION','CONSULTATION','NEGOTIATION','CLOSING','OTHER') DEFAULT NULL,
  `status` enum('SCHEDULED','CONFIRMED','IN_PROGRESS','COMPLETED','CANCELLED','RESCHEDULED','NO_SHOW') DEFAULT NULL,
  `priority` enum('LOW','MEDIUM','HIGH','URGENT') DEFAULT NULL,
  `location` varchar(500) DEFAULT NULL,
  `meeting_url` varchar(500) DEFAULT NULL,
  `meeting_id` varchar(100) DEFAULT NULL,
  `meeting_password` varchar(100) DEFAULT NULL,
  `lead_id` int(11) DEFAULT NULL,
  `lead_name` varchar(255) DEFAULT NULL,
  `lead_email` varchar(255) DEFAULT NULL,
  `lead_phone` varchar(50) DEFAULT NULL,
  `lead_company` varchar(255) DEFAULT NULL,
  `deal_value` float DEFAULT NULL,
  `deal_stage` varchar(100) DEFAULT NULL,
  `deal_probability` float DEFAULT NULL,
  `recurrence_type` enum('NONE','DAILY','WEEKLY','MONTHLY','YEARLY','CUSTOM') DEFAULT NULL,
  `recurrence_interval` int(11) DEFAULT NULL,
  `recurrence_end_date` datetime DEFAULT NULL,
  `recurrence_count` int(11) DEFAULT NULL,
  `parent_event_id` int(11) DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  `notes` text DEFAULT NULL,
  `tags` varchar(500) DEFAULT NULL,
  `custom_fields` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`custom_fields`)),
  `reminder_minutes` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`reminder_minutes`)),
  `email_reminders` tinyint(1) DEFAULT NULL,
  `sms_reminders` tinyint(1) DEFAULT NULL,
  `user_id` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `event_attendees`
--

CREATE TABLE `event_attendees` (
  `id` int(11) NOT NULL,
  `event_id` int(11) NOT NULL,
  `name` varchar(255) NOT NULL,
  `email` varchar(255) NOT NULL,
  `phone` varchar(50) DEFAULT NULL,
  `company` varchar(255) DEFAULT NULL,
  `job_title` varchar(255) DEFAULT NULL,
  `lead_id` int(11) DEFAULT NULL,
  `status` enum('PENDING','ACCEPTED','DECLINED','TENTATIVE','NO_RESPONSE') DEFAULT NULL,
  `is_organizer` tinyint(1) DEFAULT NULL,
  `is_required` tinyint(1) DEFAULT NULL,
  `response_datetime` datetime DEFAULT NULL,
  `response_notes` text DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  `user_id` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `event_categories`
--

CREATE TABLE `event_categories` (
  `id` int(11) NOT NULL,
  `name` varchar(100) NOT NULL,
  `description` text DEFAULT NULL,
  `color` varchar(7) DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  `created_by` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `event_reminders`
--

CREATE TABLE `event_reminders` (
  `id` int(11) NOT NULL,
  `event_id` int(11) NOT NULL,
  `minutes_before` int(11) NOT NULL,
  `reminder_type` varchar(50) NOT NULL,
  `is_sent` tinyint(1) DEFAULT NULL,
  `sent_at` datetime DEFAULT NULL,
  `scheduled_for` datetime NOT NULL,
  `recipient_email` varchar(255) DEFAULT NULL,
  `recipient_phone` varchar(50) DEFAULT NULL,
  `recipient_name` varchar(255) DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  `user_id` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `event_templates`
--

CREATE TABLE `event_templates` (
  `id` int(11) NOT NULL,
  `name` varchar(255) NOT NULL,
  `description` text DEFAULT NULL,
  `event_type` enum('MEETING','CALL','APPOINTMENT','FOLLOW_UP','DEMO','PRESENTATION','CONSULTATION','NEGOTIATION','CLOSING','OTHER') DEFAULT NULL,
  `duration_minutes` int(11) DEFAULT NULL,
  `location` varchar(500) DEFAULT NULL,
  `meeting_url` varchar(500) DEFAULT NULL,
  `title_template` varchar(255) DEFAULT NULL,
  `description_template` text DEFAULT NULL,
  `priority` enum('LOW','MEDIUM','HIGH','URGENT') DEFAULT NULL,
  `reminder_minutes` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`reminder_minutes`)),
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  `user_id` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `lead_event_mappings`
--

CREATE TABLE `lead_event_mappings` (
  `id` int(11) NOT NULL,
  `lead_id` int(11) NOT NULL,
  `event_id` int(11) NOT NULL,
  `relationship_type` varchar(50) NOT NULL,
  `notes` text DEFAULT NULL,
  `created_at` datetime NOT NULL,
  `user_id` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Indexes for dumped tables
--

--
-- Indexes for table `calendars`
--
ALTER TABLE `calendars`
  ADD PRIMARY KEY (`id`),
  ADD KEY `ix_calendars_name` (`name`),
  ADD KEY `ix_calendars_id` (`id`),
  ADD KEY `ix_calendars_owner_id` (`owner_id`);

--
-- Indexes for table `events`
--
ALTER TABLE `events`
  ADD PRIMARY KEY (`id`),
  ADD KEY `parent_event_id` (`parent_event_id`),
  ADD KEY `ix_events_id` (`id`),
  ADD KEY `ix_events_start_datetime` (`start_datetime`),
  ADD KEY `ix_events_priority` (`priority`),
  ADD KEY `ix_events_end_datetime` (`end_datetime`),
  ADD KEY `ix_events_event_type` (`event_type`),
  ADD KEY `ix_events_title` (`title`),
  ADD KEY `ix_events_lead_id` (`lead_id`),
  ADD KEY `ix_events_status` (`status`);

--
-- Indexes for table `event_attendees`
--
ALTER TABLE `event_attendees`
  ADD PRIMARY KEY (`id`),
  ADD KEY `ix_event_attendees_event_id` (`event_id`),
  ADD KEY `ix_event_attendees_id` (`id`),
  ADD KEY `ix_event_attendees_email` (`email`),
  ADD KEY `ix_event_attendees_lead_id` (`lead_id`);

--
-- Indexes for table `event_categories`
--
ALTER TABLE `event_categories`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `ix_event_categories_name` (`name`),
  ADD KEY `ix_event_categories_id` (`id`);

--
-- Indexes for table `event_reminders`
--
ALTER TABLE `event_reminders`
  ADD PRIMARY KEY (`id`),
  ADD KEY `ix_event_reminders_scheduled_for` (`scheduled_for`),
  ADD KEY `ix_event_reminders_event_id` (`event_id`),
  ADD KEY `ix_event_reminders_id` (`id`);

--
-- Indexes for table `event_templates`
--
ALTER TABLE `event_templates`
  ADD PRIMARY KEY (`id`),
  ADD KEY `ix_event_templates_id` (`id`),
  ADD KEY `ix_event_templates_name` (`name`);

--
-- Indexes for table `lead_event_mappings`
--
ALTER TABLE `lead_event_mappings`
  ADD PRIMARY KEY (`id`),
  ADD KEY `ix_lead_event_mappings_id` (`id`),
  ADD KEY `ix_lead_event_mappings_event_id` (`event_id`),
  ADD KEY `ix_lead_event_mappings_lead_id` (`lead_id`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `calendars`
--
ALTER TABLE `calendars`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `events`
--
ALTER TABLE `events`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=27;

--
-- AUTO_INCREMENT for table `event_attendees`
--
ALTER TABLE `event_attendees`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=13;

--
-- AUTO_INCREMENT for table `event_categories`
--
ALTER TABLE `event_categories`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `event_reminders`
--
ALTER TABLE `event_reminders`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=20;

--
-- AUTO_INCREMENT for table `event_templates`
--
ALTER TABLE `event_templates`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `lead_event_mappings`
--
ALTER TABLE `lead_event_mappings`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=22;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `events`
--
ALTER TABLE `events`
  ADD CONSTRAINT `events_ibfk_1` FOREIGN KEY (`parent_event_id`) REFERENCES `events` (`id`);

--
-- Constraints for table `event_attendees`
--
ALTER TABLE `event_attendees`
  ADD CONSTRAINT `event_attendees_ibfk_1` FOREIGN KEY (`event_id`) REFERENCES `events` (`id`);

--
-- Constraints for table `event_reminders`
--
ALTER TABLE `event_reminders`
  ADD CONSTRAINT `event_reminders_ibfk_1` FOREIGN KEY (`event_id`) REFERENCES `events` (`id`);

--
-- Constraints for table `lead_event_mappings`
--
ALTER TABLE `lead_event_mappings`
  ADD CONSTRAINT `lead_event_mappings_ibfk_1` FOREIGN KEY (`event_id`) REFERENCES `events` (`id`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
