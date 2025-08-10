-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Jul 17, 2025 at 12:08 PM
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
-- Database: `outreach_db`
--

-- --------------------------------------------------------

--
-- Table structure for table `bulk_message_groups`
--

CREATE TABLE `bulk_message_groups` (
  `id` int(11) NOT NULL,
  `user_id` varchar(255) DEFAULT NULL,
  `platform_id` int(11) NOT NULL,
  `campaign_id` int(11) NOT NULL,
  `total_leads` int(11) NOT NULL,
  `success_count` int(11) DEFAULT NULL,
  `failed_count` int(11) DEFAULT NULL,
  `subject` varchar(255) DEFAULT NULL,
  `is_resend` tinyint(1) DEFAULT NULL,
  `parent_group_id` int(11) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `campaign_leads`
--

CREATE TABLE `campaign_leads` (
  `id` int(11) NOT NULL,
  `campaign_id` int(11) NOT NULL,
  `lead_id` int(11) NOT NULL,
  `added_at` timestamp NULL DEFAULT current_timestamp(),
  `status` varchar(50) NOT NULL,
  `user_id` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `conversations`
--

CREATE TABLE `conversations` (
  `id` int(11) NOT NULL,
  `lead_id` int(11) NOT NULL,
  `platform_id` int(11) NOT NULL,
  `last_message_at` timestamp NULL DEFAULT NULL,
  `status` varchar(50) NOT NULL,
  `subject` varchar(255) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NULL DEFAULT current_timestamp(),
  `user_id` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `conversation_messages`
--

CREATE TABLE `conversation_messages` (
  `id` int(11) NOT NULL,
  `conversation_id` int(11) NOT NULL,
  `outreach_message_id` int(11) DEFAULT NULL,
  `direction` varchar(10) NOT NULL,
  `message_content` text NOT NULL,
  `sent_at` timestamp NULL DEFAULT current_timestamp(),
  `platform_message_id` varchar(255) DEFAULT NULL,
  `sender_identifier` varchar(255) DEFAULT NULL,
  `recipient_identifier` varchar(255) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NULL DEFAULT current_timestamp(),
  `user_id` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `lead_platform_validations`
--

CREATE TABLE `lead_platform_validations` (
  `id` int(11) NOT NULL,
  `lead_id` int(11) NOT NULL,
  `platform_id` int(11) NOT NULL,
  `is_valid` tinyint(1) NOT NULL,
  `validation_date` timestamp NULL DEFAULT current_timestamp(),
  `details` text DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NULL DEFAULT current_timestamp(),
  `user_id` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `outreach_campaigns`
--

CREATE TABLE `outreach_campaigns` (
  `id` int(11) NOT NULL,
  `name` varchar(255) NOT NULL,
  `description` text DEFAULT NULL,
  `start_date` date DEFAULT NULL,
  `end_date` date DEFAULT NULL,
  `status` varchar(50) NOT NULL,
  `created_at` timestamp NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NULL DEFAULT current_timestamp(),
  `user_id` varchar(255) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `outreach_messages`
--

CREATE TABLE `outreach_messages` (
  `id` int(11) NOT NULL,
  `lead_id` int(11) NOT NULL,
  `platform_id` int(11) NOT NULL,
  `sender_id` int(11) NOT NULL,
  `message_content` text NOT NULL,
  `sent_at` timestamp NULL DEFAULT current_timestamp(),
  `status` varchar(50) NOT NULL,
  `platform_message_id` varchar(255) DEFAULT NULL,
  `error_message` text DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NULL DEFAULT current_timestamp(),
  `campaign_id` int(11) DEFAULT NULL,
  `bulk_group_id` int(11) DEFAULT NULL,
  `subject` varchar(255) DEFAULT NULL,
  `user_id` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `outreach_platforms`
--

CREATE TABLE `outreach_platforms` (
  `id` int(11) NOT NULL,
  `name` varchar(255) NOT NULL,
  `description` text DEFAULT NULL,
  `user_id` varchar(255) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `outreach_templates`
--

CREATE TABLE `outreach_templates` (
  `id` int(11) NOT NULL,
  `name` varchar(255) NOT NULL,
  `subject` varchar(255) DEFAULT NULL,
  `content` text NOT NULL,
  `created_at` timestamp NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NULL DEFAULT current_timestamp(),
  `user_id` varchar(255) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `user_platform_credentials`
--

CREATE TABLE `user_platform_credentials` (
  `id` int(11) NOT NULL,
  `user_id` varchar(255) DEFAULT NULL,
  `platform_id` int(11) NOT NULL,
  `username` varchar(255) NOT NULL,
  `password` text DEFAULT NULL,
  `expires_at` timestamp NULL DEFAULT NULL,
  `platform_user_id` varchar(255) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Indexes for dumped tables
--

--
-- Indexes for table `bulk_message_groups`
--
ALTER TABLE `bulk_message_groups`
  ADD PRIMARY KEY (`id`),
  ADD KEY `platform_id` (`platform_id`),
  ADD KEY `campaign_id` (`campaign_id`),
  ADD KEY `parent_group_id` (`parent_group_id`),
  ADD KEY `ix_bulk_message_groups_id` (`id`);

--
-- Indexes for table `campaign_leads`
--
ALTER TABLE `campaign_leads`
  ADD PRIMARY KEY (`id`),
  ADD KEY `campaign_id` (`campaign_id`),
  ADD KEY `ix_campaign_leads_id` (`id`);

--
-- Indexes for table `conversations`
--
ALTER TABLE `conversations`
  ADD PRIMARY KEY (`id`),
  ADD KEY `platform_id` (`platform_id`),
  ADD KEY `ix_conversations_id` (`id`);

--
-- Indexes for table `conversation_messages`
--
ALTER TABLE `conversation_messages`
  ADD PRIMARY KEY (`id`),
  ADD KEY `conversation_id` (`conversation_id`),
  ADD KEY `outreach_message_id` (`outreach_message_id`),
  ADD KEY `ix_conversation_messages_id` (`id`);

--
-- Indexes for table `lead_platform_validations`
--
ALTER TABLE `lead_platform_validations`
  ADD PRIMARY KEY (`id`),
  ADD KEY `platform_id` (`platform_id`),
  ADD KEY `ix_lead_platform_validations_id` (`id`);

--
-- Indexes for table `outreach_campaigns`
--
ALTER TABLE `outreach_campaigns`
  ADD PRIMARY KEY (`id`),
  ADD KEY `ix_outreach_campaigns_id` (`id`);

--
-- Indexes for table `outreach_messages`
--
ALTER TABLE `outreach_messages`
  ADD PRIMARY KEY (`id`),
  ADD KEY `platform_id` (`platform_id`),
  ADD KEY `ix_outreach_messages_id` (`id`),
  ADD KEY `fk_outreach_messages_campaign_id` (`campaign_id`),
  ADD KEY `bulk_message_groups_id` (`bulk_group_id`),
  ADD KEY `outreach_messages_sender_id_fkey` (`sender_id`);

--
-- Indexes for table `outreach_platforms`
--
ALTER TABLE `outreach_platforms`
  ADD PRIMARY KEY (`id`),
  ADD KEY `ix_outreach_platforms_id` (`id`);

--
-- Indexes for table `outreach_templates`
--
ALTER TABLE `outreach_templates`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `user_platform_credentials`
--
ALTER TABLE `user_platform_credentials`
  ADD PRIMARY KEY (`id`),
  ADD KEY `platform_id` (`platform_id`),
  ADD KEY `ix_user_platform_credentials_id` (`id`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `bulk_message_groups`
--
ALTER TABLE `bulk_message_groups`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=33;

--
-- AUTO_INCREMENT for table `campaign_leads`
--
ALTER TABLE `campaign_leads`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=41;

--
-- AUTO_INCREMENT for table `conversations`
--
ALTER TABLE `conversations`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=10;

--
-- AUTO_INCREMENT for table `conversation_messages`
--
ALTER TABLE `conversation_messages`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `lead_platform_validations`
--
ALTER TABLE `lead_platform_validations`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT for table `outreach_campaigns`
--
ALTER TABLE `outreach_campaigns`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=15;

--
-- AUTO_INCREMENT for table `outreach_messages`
--
ALTER TABLE `outreach_messages`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=97;

--
-- AUTO_INCREMENT for table `outreach_platforms`
--
ALTER TABLE `outreach_platforms`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=70;

--
-- AUTO_INCREMENT for table `outreach_templates`
--
ALTER TABLE `outreach_templates`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=25;

--
-- AUTO_INCREMENT for table `user_platform_credentials`
--
ALTER TABLE `user_platform_credentials`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=18;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `bulk_message_groups`
--
ALTER TABLE `bulk_message_groups`
  ADD CONSTRAINT `bulk_message_groups_ibfk_1` FOREIGN KEY (`platform_id`) REFERENCES `outreach_platforms` (`id`),
  ADD CONSTRAINT `bulk_message_groups_ibfk_2` FOREIGN KEY (`campaign_id`) REFERENCES `outreach_campaigns` (`id`),
  ADD CONSTRAINT `bulk_message_groups_ibfk_3` FOREIGN KEY (`parent_group_id`) REFERENCES `bulk_message_groups` (`id`);

--
-- Constraints for table `campaign_leads`
--
ALTER TABLE `campaign_leads`
  ADD CONSTRAINT `campaign_leads_ibfk_1` FOREIGN KEY (`campaign_id`) REFERENCES `outreach_campaigns` (`id`);

--
-- Constraints for table `conversations`
--
ALTER TABLE `conversations`
  ADD CONSTRAINT `conversations_ibfk_1` FOREIGN KEY (`platform_id`) REFERENCES `outreach_platforms` (`id`);

--
-- Constraints for table `conversation_messages`
--
ALTER TABLE `conversation_messages`
  ADD CONSTRAINT `conversation_messages_ibfk_1` FOREIGN KEY (`conversation_id`) REFERENCES `conversations` (`id`),
  ADD CONSTRAINT `conversation_messages_ibfk_2` FOREIGN KEY (`outreach_message_id`) REFERENCES `outreach_messages` (`id`);

--
-- Constraints for table `lead_platform_validations`
--
ALTER TABLE `lead_platform_validations`
  ADD CONSTRAINT `lead_platform_validations_ibfk_1` FOREIGN KEY (`platform_id`) REFERENCES `outreach_platforms` (`id`);

--
-- Constraints for table `outreach_messages`
--
ALTER TABLE `outreach_messages`
  ADD CONSTRAINT `fk_bulk_message_groups` FOREIGN KEY (`bulk_group_id`) REFERENCES `bulk_message_groups` (`id`) ON DELETE SET NULL,
  ADD CONSTRAINT `fk_outreach_messages_campaign_id` FOREIGN KEY (`campaign_id`) REFERENCES `outreach_campaigns` (`id`) ON DELETE SET NULL ON UPDATE CASCADE,
  ADD CONSTRAINT `outreach_messages_ibfk_1` FOREIGN KEY (`platform_id`) REFERENCES `outreach_platforms` (`id`),
  ADD CONSTRAINT `outreach_messages_ibfk_2` FOREIGN KEY (`sender_id`) REFERENCES `user_platform_credentials` (`id`),
  ADD CONSTRAINT `outreach_messages_sender_id_fkey` FOREIGN KEY (`sender_id`) REFERENCES `user_platform_credentials` (`id`) ON DELETE CASCADE;

--
-- Constraints for table `user_platform_credentials`
--
ALTER TABLE `user_platform_credentials`
  ADD CONSTRAINT `user_platform_credentials_ibfk_1` FOREIGN KEY (`platform_id`) REFERENCES `outreach_platforms` (`id`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
