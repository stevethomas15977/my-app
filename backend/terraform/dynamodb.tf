# AFE session table
resource "aws_dynamodb_table" "havac_bid_submittal_tenant_table" {
  name           = "hvac-bid-submittal-tenant-table"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "tenant_id"

  attribute {
    name = "tenant_id"
    type = "S"
  }

  point_in_time_recovery {
    enabled = true
  }
}