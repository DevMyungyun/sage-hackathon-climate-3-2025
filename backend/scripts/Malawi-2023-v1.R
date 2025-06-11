# Load necessary libraries
library(dplyr)
library(readr)
library(lubridate)

# Read the CSV file
data <- read_csv("~/Downloads/Malawi_Met_Data_2023.csv")

# Convert 'date' to Date type (format is day/month/year)
data <- data %>%
  mutate(date = dmy(date),
         year_month = format(date, "%Y-%m"))  # e.g., "2023-01"

# Aggregate: mean value by station, element, and month
monthly_agg <- data %>%
  group_by(station_id, element_abbrv, year_month) %>%
  summarise(mean_value = mean(value, na.rm = TRUE), .groups = 'drop')

# Export to CSV
write_csv(monthly_agg, "~/Downloads/malawi_monthly_aggregated.csv")
