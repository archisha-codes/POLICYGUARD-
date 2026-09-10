# CloudWatch Alarms for PolicyGuard Kinesis Stream
# Monitor transaction throughput, errors, and consumer lag

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# Variables
variable "aws_region" {
  description = "AWS region"
  default     = "ap-south-1"
}

variable "stream_name" {
  description = "Kinesis stream name"
  default     = "policyguard-transaction-stream"
}

variable "sns_topic_arn" {
  description = "SNS topic ARN for alarm notifications"
  type        = string
}

# Output for verification
output "kinesis_alarms" {
  value       = aws_cloudwatch_metric_alarm.kinesis_alarms
  description = "Created CloudWatch alarms"
}

# ==============================================================
# KINESIS STREAM METRICS
# ==============================================================

# Monitor incoming records - should be consistently high
resource "aws_cloudwatch_metric_alarm" "incoming_records_low" {
  alarm_name          = "${var.stream_name}-incoming-records-low"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "IncomingRecords"
  namespace           = "AWS/Kinesis"
  period              = "300"  # 5 minutes
  statistic           = "Sum"
  threshold           = "100"  # Less than 100 records in 5 min
  alarm_description   = "Alert when incoming records drop below threshold (potential data loss)"
  alarm_actions       = [var.sns_topic_arn]

  dimensions = {
    StreamName = var.stream_name
  }
}

# Monitor incoming data bytes - measure throughput
resource "aws_cloudwatch_metric_alarm" "incoming_data_bytes" {
  alarm_name          = "${var.stream_name}-high-throughput"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "IncomingBytes"
  namespace           = "AWS/Kinesis"
  period              = "60"
  statistic           = "Sum"
  threshold           = "900000"  # >900KB in 1 minute
  alarm_description   = "Alert when throughput exceeds safe limits"
  alarm_actions       = [var.sns_topic_arn]

  dimensions = {
    StreamName = var.stream_name
  }
}

# ==============================================================
# ITERATOR AGE MONITORING
# ==============================================================

# Monitor iterator age - consumer lag indicator
resource "aws_cloudwatch_metric_alarm" "iterator_age_high" {
  alarm_name          = "${var.stream_name}-iterator-age-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "GetRecords.IteratorAgeMilliseconds"
  namespace           = "AWS/Kinesis"
  period              = "300"
  statistic           = "Maximum"
  threshold           = "60000"  # 1 minute
  alarm_description   = "Alert when consumer falls behind (>1 minute lag)"
  alarm_actions       = [var.sns_topic_arn]

  dimensions = {
    StreamName = var.stream_name
  }
}

# ==============================================================
# ERROR MONITORING
# ==============================================================

# Monitor GetRecords errors
resource "aws_cloudwatch_metric_alarm" "get_records_errors" {
  alarm_name          = "${var.stream_name}-get-records-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "GetRecords.LatencyMs"
  namespace           = "AWS/Kinesis"
  period              = "300"
  statistic           = "Average"
  threshold           = "100"  # >100ms average
  alarm_description   = "Alert when GetRecords latency increases (potential throttling)"
  alarm_actions       = [var.sns_topic_arn]

  dimensions = {
    StreamName = var.stream_name
  }
}

# Monitor PutRecord errors
resource "aws_cloudwatch_metric_alarm" "put_record_errors" {
  alarm_name          = "${var.stream_name}-put-record-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "UserErrors"
  namespace           = "AWS/Kinesis"
  period              = "300"
  statistic           = "Sum"
  threshold           = "10"
  alarm_description   = "Alert on PutRecord user errors (validation failures)"
  alarm_actions       = [var.sns_topic_arn]

  dimensions = {
    StreamName = var.stream_name
  }
}

# Monitor system errors
resource "aws_cloudwatch_metric_alarm" "system_errors" {
  alarm_name          = "${var.stream_name}-system-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "SystemErrors"
  namespace           = "AWS/Kinesis"
  period              = "60"
  statistic           = "Sum"
  threshold           = "5"
  alarm_description   = "Alert on system-level Kinesis errors"
  alarm_actions       = [var.sns_topic_arn]
  treat_missing_data  = "notBreaching"

  dimensions = {
    StreamName = var.stream_name
  }
}

# ==============================================================
# LATENCY MONITORING
# ==============================================================

# Monitor PutRecord latency
resource "aws_cloudwatch_metric_alarm" "put_record_latency" {
  alarm_name          = "${var.stream_name}-put-record-latency"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "PutRecord.LatencyMs"
  namespace           = "AWS/Kinesis"
  period              = "300"
  statistic           = "Average"
  threshold           = "50"  # >50ms average
  alarm_description   = "Alert when PutRecord latency increases"
  alarm_actions       = [var.sns_topic_arn]

  dimensions = {
    StreamName = var.stream_name
  }
}

# ==============================================================
# COMPOSITE ALARMS
# ==============================================================

# Overall stream health alarm
resource "aws_cloudwatch_composite_alarm" "stream_health" {
  alarm_name          = "${var.stream_name}-overall-health"
  alarm_description   = "Composite alarm for overall Kinesis stream health"
  actions_enabled     = true
  alarm_actions       = [var.sns_topic_arn]

  alarm_rule = join(" OR ", [
    "arn:aws:cloudwatch:${var.aws_region}:ACCOUNT_ID:alarm:${aws_cloudwatch_metric_alarm.iterator_age_high.alarm_name}",
    "arn:aws:cloudwatch:${var.aws_region}:ACCOUNT_ID:alarm:${aws_cloudwatch_metric_alarm.system_errors.alarm_name}",
    "arn:aws:cloudwatch:${var.aws_region}:ACCOUNT_ID:alarm:${aws_cloudwatch_metric_alarm.put_record_latency.alarm_name}"
  ])
}

# ==============================================================
# DASHBOARD
# ==============================================================

resource "aws_cloudwatch_dashboard" "kinesis_monitoring" {
  dashboard_name = "${var.stream_name}-monitoring"

  dashboard_body = jsonencode({
    widgets = [
      {
        type = "metric"
        properties = {
          metrics = [
            ["AWS/Kinesis", "IncomingRecords", { StreamName = var.stream_name }],
            [".", "IncomingBytes", { StreamName = var.stream_name }],
            [".", "GetRecords.IteratorAgeMilliseconds", { StreamName = var.stream_name }]
          ]
          period = 300
          stat   = "Average"
          region = var.aws_region
          title  = "Stream Activity"
        }
      },
      {
        type = "metric"
        properties = {
          metrics = [
            ["AWS/Kinesis", "UserErrors", { StreamName = var.stream_name }],
            [".", "SystemErrors", { StreamName = var.stream_name }]
          ]
          period = 60
          stat   = "Sum"
          region = var.aws_region
          title  = "Error Metrics"
        }
      },
      {
        type = "metric"
        properties = {
          metrics = [
            ["AWS/Kinesis", "PutRecord.LatencyMs", { StreamName = var.stream_name }],
            [".", "GetRecords.LatencyMs", { StreamName = var.stream_name }]
          ]
          period = 300
          stat   = "Average"
          region = var.aws_region
          title  = "Latency Metrics"
        }
      }
    ]
  })
}

# ==============================================================
# USAGE NOTES
# ==============================================================
# Deploy with:
# terraform init
# terraform plan
# terraform apply -var="sns_topic_arn=arn:aws:sns:ap-south-1:ACCOUNT_ID:your-topic"
#
# All alarms send notifications to the specified SNS topic
