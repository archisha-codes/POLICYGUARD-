# PAWAN: Amazon Bedrock Infrastructure Setup Guide

## Your Role: Infrastructure & Cloud Foundation

You are responsible for configuring AWS Bedrock, setting up IAM permissions, and verifying connectivity. This guide walks you through each step.

**Estimated Time**: 20-30 minutes
**Deadline**: Already migrated; execute these steps to complete Phase 1

---

## ✅ Task Checklist

- [ ] Enable Amazon Nova models in Bedrock console
- [ ] Create/update IAM policy for bedrock:InvokeModel
- [ ] Attach policy to EC2/Lambda/ECS role
- [ ] Set environment variables (BEDROCK_REGION, NOVA_MODEL_ID)
- [ ] Run health check to verify connectivity
- [ ] Document the setup for team reference

---

## Step 1: Enable Amazon Nova in Bedrock Console

### 1.1 Open AWS Bedrock Console

1. Go to AWS Console: https://console.aws.amazon.com/
2. Search for **"Bedrock"** in the service search bar
3. Click **Amazon Bedrock** (ensure you're in **us-east-1** region)

### 1.2 Enable Nova Models

1. In the left sidebar, click **Model access**
2. Look for **Amazon** section (or search for "Nova")
3. Find **Amazon Nova Micro**, **Amazon Nova Lite**, **Amazon Nova Pro**
4. Click **Manage model access** button
5. Check the boxes for:
   - ✅ `amazon.nova-micro-v1:0` (Recommended: Fastest, cheapest)
   - ✅ `amazon.nova-lite-v1:0` (Optional: Mid-tier)
   - ✅ `amazon.nova-pro-v1:0` (Optional: Highest quality)
6. Click **Save changes** at the bottom
7. Wait 2-3 minutes for models to be enabled

**Status Check**: You should see a green checkmark "Access granted" next to each model

---

## Step 2: Create IAM Policy for Bedrock

### 2.1 Go to IAM Console

1. Open IAM Console: https://console.aws.amazon.com/iam/
2. Click **Policies** in the left sidebar
3. Click **Create policy**

### 2.2 Create the Policy

**Option A: Using JSON Editor (Recommended)**

1. Click **JSON** tab
2. Paste this policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "BedrockNovaInvoke",
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream"
      ],
      "Resource": "arn:aws:bedrock:us-east-1::foundation-model/amazon.nova-*"
    },
    {
      "Sid": "BedrockListModels",
      "Effect": "Allow",
      "Action": "bedrock:ListFoundationModels",
      "Resource": "*"
    }
  ]
}
```

3. Click **Next**
4. Name the policy: `PolicyGuard-Bedrock-Nova-Access`
5. Add description: "Allows POLICYGUARD backend to invoke Amazon Nova models on Bedrock"
6. Click **Create policy**

**Option B: Using Visual Editor**

1. Click **Visual editor** tab
2. Click **Add statement**
3. Set:
   - **Service**: Bedrock
   - **Actions**: Select "bedrock:InvokeModel" and "bedrock:InvokeModelWithResponseStream"
   - **Resources**: Specific ARN → `arn:aws:bedrock:us-east-1::foundation-model/amazon.nova-*`
4. Add another statement for `bedrock:ListFoundationModels` with "All resources"
5. Click **Next**, name it, and create

---

## Step 3: Attach Policy to Your Compute Role

### 3.1 Identify Your Compute Role

Determine which role your backend runs under:

**If running on EC2:**
```bash
# SSH into EC2 instance
ssh -i your-key.pem ec2-user@your-ec2-ip

# Check role
curl http://169.254.169.254/latest/meta-data/iam/security-credentials/
# Output: RoleName (e.g., policyguard-ec2-role)
```

**If running on Lambda:**
- Role name is shown in Lambda function → Configuration → Execution role
- E.g., `policyguard-lambda-role`

**If running on ECS:**
- Role name is in task definition → Task role ARN
- E.g., `policyguard-ecs-task-role`

### 3.2 Attach Policy to Role

1. Go to IAM Console → Roles
2. Search for your role (e.g., `policyguard-ec2-role`)
3. Click the role name
4. Click **Add permissions** → **Attach policies**
5. Search for `PolicyGuard-Bedrock-Nova-Access`
6. Check the box and click **Attach policies**

**Verification**: You should see the policy listed under "Permissions" tab

---

## Step 4: Set Environment Variables

Set these variables in your deployment environment:

### 4.1 On EC2 Instance

```bash
# SSH into your EC2 instance
ssh -i your-key.pem ec2-user@your-instance-ip

# Add to ~/.bashrc or ~/.bash_profile
echo 'export BEDROCK_REGION="us-east-1"' >> ~/.bashrc
echo 'export NOVA_MODEL_ID="amazon.nova-micro-v1:0"' >> ~/.bashrc
source ~/.bashrc

# Verify
echo $BEDROCK_REGION
echo $NOVA_MODEL_ID
```

**For SystemD Service:**
```bash
# Edit your service file
sudo nano /etc/systemd/system/policyguard.service

# Add under [Service] section:
Environment="BEDROCK_REGION=us-east-1"
Environment="NOVA_MODEL_ID=amazon.nova-micro-v1:0"

# Restart service
sudo systemctl daemon-reload
sudo systemctl restart policyguard
```

### 4.2 On AWS Lambda

1. Go to AWS Lambda Console
2. Find your function (e.g., `policyguard-compliance-api`)
3. Click **Configuration** → **Environment variables**
4. Click **Edit**
5. Add:
   - Key: `BEDROCK_REGION`, Value: `us-east-1`
   - Key: `NOVA_MODEL_ID`, Value: `amazon.nova-micro-v1:0`
6. Click **Save**
7. Lambda auto-redeploys

### 4.3 On ECS Task Definition

1. Go to ECS Console → Task Definitions
2. Find your task definition (e.g., `policyguard-backend-task`)
3. Click **Create new revision**
4. Find your container → **Environment variables**
5. Add:
   ```
   BEDROCK_REGION=us-east-1
   NOVA_MODEL_ID=amazon.nova-micro-v1:0
   ```
6. Click **Create**
7. Update your service to use the new task definition

### 4.4 Using AWS Systems Manager Parameter Store (Optional but Recommended)

```bash
# Store in Parameter Store
aws ssm put-parameter \
  --name "/policyguard/bedrock/region" \
  --value "us-east-1" \
  --type "String" \
  --region us-east-1

aws ssm put-parameter \
  --name "/policyguard/bedrock/model-id" \
  --value "amazon.nova-micro-v1:0" \
  --type "String" \
  --region us-east-1

# Retrieve in Python
import boto3
ssm = boto3.client('ssm', region_name='us-east-1')
region = ssm.get_parameter(Name='/policyguard/bedrock/region')['Parameter']['Value']
model_id = ssm.get_parameter(Name='/policyguard/bedrock/model-id')['Parameter']['Value']
```

---

## Step 5: Verify Setup with Health Check

### 5.1 Local Testing (Before deployment)

```bash
# SSH into EC2 or login to Lambda test console

# Create a test script
cat > test_bedrock.py << 'EOF'
from services.bedrock_client import health_check
import json

print("Testing Bedrock connectivity...")
result = health_check()
print(json.dumps(result, indent=2))

if result['status'] == 'success':
    print("\n✅ SUCCESS: Bedrock is connected!")
else:
    print("\n❌ ERROR: Check the error message above")
EOF

# Run test
python test_bedrock.py
```

**Expected Output:**
```json
{
  "status": "success",
  "text": "{\"status\": \"ok\", \"model\": \"nova\"}",
  "tokens_used": "45",
  "timestamp": "2026-01-13T10:30:45.123456"
}
```

### 5.2 Common Errors & Fixes

**Error 1: "ValidationException: Could not validate the followed model identifier"**
```
Cause: Nova models not enabled in Bedrock console
Fix: Go to Model access and enable amazon.nova-* models
```

**Error 2: "AccessDenied: User: arn:aws:iam::... is not authorized to perform: bedrock:InvokeModel"**
```
Cause: IAM policy not attached to role
Fix: 
  1. Verify role name (check EC2 metadata/Lambda config)
  2. Attach PolicyGuard-Bedrock-Nova-Access policy
  3. Wait 5 minutes for IAM propagation
```

**Error 3: "NoCredentialsError: Unable to locate credentials"**
```
Cause: IAM role not assigned to EC2/Lambda/ECS
Fix:
  1. Ensure IAM role is attached to compute resource
  2. For EC2: aws ec2 describe-instances --instance-ids i-xxx
     Look for "IamInstanceProfile"
  3. For Lambda: Check Execution role in Configuration
```

**Error 4: "Region us-east-1 not available for Bedrock"**
```
Cause: Using wrong region
Fix: Use us-east-1 or us-west-2 (primary Bedrock regions)
Set: export BEDROCK_REGION="us-east-1"
```

---

## Step 6: Advanced Configuration (Optional)

### 6.1 Switch Between Nova Models

```bash
# Micro (fastest, cheapest) - Default
export NOVA_MODEL_ID="amazon.nova-micro-v1:0"

# Lite (balanced)
export NOVA_MODEL_ID="amazon.nova-lite-v1:0"

# Pro (highest quality)
export NOVA_MODEL_ID="amazon.nova-pro-v1:0"
```

### 6.2 CloudWatch Monitoring

```bash
# Create CloudWatch alarm for Bedrock failures
aws cloudwatch put-metric-alarm \
  --alarm-name "policyguard-bedrock-failures" \
  --alarm-description "Alert on Bedrock invocation failures" \
  --metric-name "InvocationErrors" \
  --namespace "AWS/Bedrock" \
  --statistic "Sum" \
  --period 300 \
  --threshold 5 \
  --comparison-operator "GreaterThanOrEqualToThreshold"
```

### 6.3 Cost Monitoring

```bash
# Enable cost tracking in AWS Billing
# Go to: AWS Billing Console → Cost Explorer → Filter by Bedrock service
# Expected cost for 1M transactions/month: $300-400 (Nova Micro)
```

---

## Step 7: Document Your Setup

Create a runbook for the team:

```markdown
## POLICYGUARD Bedrock Setup Summary

**Completed by**: Pawan Dubey
**Date**: January 2026

### AWS Configuration
- **Region**: us-east-1
- **Nova Model**: amazon.nova-micro-v1:0
- **IAM Policy**: PolicyGuard-Bedrock-Nova-Access
- **Compute Role**: [Your role name]

### Verification
- ✅ Bedrock models enabled in console
- ✅ IAM policy created and attached
- ✅ Environment variables set
- ✅ Health check passing

### Monitoring
- CloudWatch: [Link to dashboard]
- Cost Explorer: [Link to cost analysis]
```

---

## 🔗 Useful Links

- [AWS Bedrock Console](https://console.aws.amazon.com/bedrock/)
- [Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)
- [IAM Policies Guide](https://docs.aws.amazon.com/IAM/)
- [Amazon Nova Pricing](https://aws.amazon.com/bedrock/pricing/)

---

## 📞 Support

If you encounter issues:

1. Check the **Troubleshooting** section above
2. Review AWS Bedrock CloudWatch logs
3. Verify IAM permissions: `aws iam get-role-policy --role-name [YOUR_ROLE] --policy-name [POLICY_NAME]`
4. Contact Archisha (POLICYGUARD Lead) or check GitHub issues

---

**Status**: Phase 1 Complete ✅
**Next Step**: Testing team (Himansh) runs compliance tests
