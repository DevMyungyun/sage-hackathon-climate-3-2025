# Load necessary libraries
library(dplyr)
library(readr)
library(lubridate)

# Command line arguments for input and output file paths
args <- commandArgs(trailingOnly = TRUE)
input_path <- ifelse(length(args) >= 1, args[1], "/tmp/latest_dataset.csv")
output_path <- ifelse(length(args) >= 2, args[2], "/tmp/processed_dataset.csv")

# Read the CSV file
data <- read_csv(input_path)
print(str(data))  # Debug: check the structure

# Convert 'date' to Date type (format is day/month/year)
data <- data %>%
  mutate(date = parse_date_time(date, orders = c("ymd", "dmy")),
         year_month = format(date, "%Y-%m"))  # e.g., "2023-01"

# Aggregate: mean value by station, element, and month
monthly_agg <- data %>%
  group_by(station_id, element_abbrv, year_month) %>%
  summarise(mean_value = mean(value, na.rm = TRUE), .groups = 'drop')

# Write the processed data to a new CSV file
write_csv(monthly_agg, output_path)
