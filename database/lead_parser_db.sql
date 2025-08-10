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
-- Database: `lead_parser_db`
--

-- --------------------------------------------------------

--
-- Table structure for table `file_uploads`
--

CREATE TABLE `file_uploads` (
  `id` int(11) NOT NULL,
  `filename` varchar(255) NOT NULL,
  `original_filename` varchar(255) NOT NULL,
  `file_path` varchar(500) NOT NULL,
  `file_size` int(11) NOT NULL,
  `file_type` varchar(50) NOT NULL,
  `mime_type` varchar(100) DEFAULT NULL,
  `status` varchar(50) DEFAULT NULL,
  `total_rows` int(11) DEFAULT NULL,
  `processed_rows` int(11) DEFAULT NULL,
  `successful_rows` int(11) DEFAULT NULL,
  `failed_rows` int(11) DEFAULT NULL,
  `duplicate_rows` int(11) DEFAULT NULL,
  `processing_started_at` datetime DEFAULT NULL,
  `processing_completed_at` datetime DEFAULT NULL,
  `processing_duration` float DEFAULT NULL,
  `error_message` text DEFAULT NULL,
  `error_details` text DEFAULT NULL,
  `leads_created` int(11) DEFAULT NULL,
  `leads_updated` int(11) DEFAULT NULL,
  `leads_skipped` int(11) DEFAULT NULL,
  `created_at` datetime NOT NULL,
  `updated_at` datetime NOT NULL,
  `user_id` varchar(255) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `leads`
--

CREATE TABLE `leads` (
  `id` int(11) NOT NULL,
  `first_name` varchar(100) DEFAULT NULL,
  `last_name` varchar(100) DEFAULT NULL,
  `full_name` varchar(200) DEFAULT NULL,
  `company` varchar(200) DEFAULT NULL,
  `job_title` varchar(200) DEFAULT NULL,
  `industry` varchar(100) DEFAULT NULL,
  `email` varchar(255) DEFAULT NULL,
  `phone` varchar(50) DEFAULT NULL,
  `mobile` varchar(50) DEFAULT NULL,
  `website` varchar(500) DEFAULT NULL,
  `address` text DEFAULT NULL,
  `city` varchar(100) DEFAULT NULL,
  `state` varchar(100) DEFAULT NULL,
  `country` varchar(100) DEFAULT NULL,
  `postal_code` varchar(20) DEFAULT NULL,
  `linkedin_url` varchar(500) DEFAULT NULL,
  `facebook_url` varchar(500) DEFAULT NULL,
  `instagram_url` varchar(500) DEFAULT NULL,
  `twitter_url` varchar(500) DEFAULT NULL,
  `youtube_url` varchar(500) DEFAULT NULL,
  `tiktok_url` varchar(500) DEFAULT NULL,
  `lead_score` float DEFAULT NULL,
  `lead_status` varchar(50) DEFAULT NULL,
  `lead_source` varchar(100) DEFAULT NULL,
  `priority` varchar(20) DEFAULT NULL,
  `email_valid` tinyint(1) DEFAULT NULL,
  `phone_valid` tinyint(1) DEFAULT NULL,
  `social_profiles_count` int(11) DEFAULT NULL,
  `data_completeness_score` float DEFAULT NULL,
  `contacted_via_email` tinyint(1) DEFAULT NULL,
  `contacted_via_phone` tinyint(1) DEFAULT NULL,
  `contacted_via_linkedin` tinyint(1) DEFAULT NULL,
  `contacted_via_facebook` tinyint(1) DEFAULT NULL,
  `contacted_via_instagram` tinyint(1) DEFAULT NULL,
  `last_contact_date` datetime DEFAULT NULL,
  `additional_data` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`additional_data`)),
  `notes` text DEFAULT NULL,
  `tags` varchar(500) DEFAULT NULL,
  `created_at` datetime NOT NULL,
  `updated_at` datetime NOT NULL,
  `source_file_name` varchar(255) DEFAULT NULL,
  `source_file_row` int(11) DEFAULT NULL,
  `is_duplicate` tinyint(1) DEFAULT NULL,
  `duplicate_of` int(11) DEFAULT NULL,
  `file_upload_id` int(11) DEFAULT NULL,
  `user_id` varchar(255) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Indexes for dumped tables
--

--
-- Indexes for table `file_uploads`
--
ALTER TABLE `file_uploads`
  ADD PRIMARY KEY (`id`),
  ADD KEY `ix_file_uploads_id` (`id`),
  ADD KEY `idx_file_uploads_user_id` (`user_id`);

--
-- Indexes for table `leads`
--
ALTER TABLE `leads`
  ADD PRIMARY KEY (`id`),
  ADD KEY `ix_leads_full_name` (`full_name`),
  ADD KEY `ix_leads_id` (`id`),
  ADD KEY `ix_leads_last_name` (`last_name`),
  ADD KEY `ix_leads_company` (`company`),
  ADD KEY `ix_leads_first_name` (`first_name`),
  ADD KEY `ix_leads_email` (`email`),
  ADD KEY `ix_leads_file_upload_id` (`file_upload_id`),
  ADD KEY `idx_leads_user_id` (`user_id`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `file_uploads`
--
ALTER TABLE `file_uploads`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=23;

--
-- AUTO_INCREMENT for table `leads`
--
ALTER TABLE `leads`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=610;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `leads`
--
ALTER TABLE `leads`
  ADD CONSTRAINT `fk_leads_file_upload_id` FOREIGN KEY (`file_upload_id`) REFERENCES `file_uploads` (`id`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
