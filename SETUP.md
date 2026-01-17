# SportsEdgeBet - Setup Guide

Complete guide to set up your SportsEdgeBet application with authentication, payments, and affiliate tracking.

## 💰 Cost Summary

| Service | Cost |
|---------|------|
| Vercel Hosting | **FREE** (100K function invocations/month) |
| Supabase | **FREE** (500MB database, 50K auth users) |
| Cloudflare DNS | **FREE** |
| Stripe | **FREE** (2.9% + 30¢ per transaction) |
| Domain | ~$10-15/year |
| **TOTAL** | **~$1/month** (just domain cost) |

---

## 🚀 Quick Start

### Step 1: Supabase Setup (5 minutes)

1. Go to [supabase.com](https://supabase.com) and create a free account
2. Create a new project (remember your database password!)
3. Go to **SQL Editor** and run the contents of `supabase-schema.sql`
4. Go to **Settings → API** and copy:
   - Project URL → `SUPABASE_URL`
   - `anon` public key → `SUPABASE_ANON_KEY`
   - `service_role` secret key → `SUPABASE_SERVICE_KEY`

5. Go to **Authentication → Providers** and enable:
   - Email (enabled by default)
   - Google (optional - requires Google Cloud Console setup)
   - GitHub (optional - requires GitHub OAuth app)

6. Go to **Authentication → URL Configuration** and set:
   - Site URL: `https://sportsedgebet.com`
   - Redirect URLs: `https://sportsedgebet.com/account.html`

### Step 2: Stripe Setup (10 minutes)

1. Go to [stripe.com](https://stripe.com) and create a free account
2. Go to **Developers → API Keys** and copy:
   - Publishable key → `STRIPE_PUBLISHABLE_KEY`
   - Secret key → `STRIPE_SECRET_KEY`

3. Create Products in **Products → Add Product**:

   **Pro Plan:**
   - Name: "Pro Monthly"
   - Price: $29/month (recurring)
   - Copy Price ID → `STRIPE_PRICE_PRO_MONTHLY`
   
   - Add another price: $276/year (recurring)
   - Copy Price ID → `STRIPE_PRICE_PRO_YEARLY`

   **Elite Plan:**
   - Name: "Elite Monthly"  
   - Price: $79/month (recurring)
   - Copy Price ID → `STRIPE_PRICE_ELITE_MONTHLY`
   
   - Add another price: $756/year (recurring)
   - Copy Price ID → `STRIPE_PRICE_ELITE_YEARLY`

4. Set up Webhook in **Developers → Webhooks → Add Endpoint**:
   - URL: `https://sportsedgebet.com/api/stripe-webhook`
   - Events to listen for:
     - `checkout.session.completed`
     - `customer.subscription.created`
     - `customer.subscription.updated`
     - `customer.subscription.deleted`
     - `invoice.paid`
     - `invoice.payment_failed`
   - Copy Signing Secret → `STRIPE_WEBHOOK_SECRET`

### Step 3: Update Configuration

1. Edit `scripts/config.js` and replace the placeholder values:

```javascript
const CONFIG = {
    SUPABASE_URL: 'https://YOUR_PROJECT.supabase.co',
    SUPABASE_ANON_KEY: 'your-anon-key-here',
    STRIPE_PUBLISHABLE_KEY: 'pk_live_xxxxx', // or pk_test_xxxxx for testing
    STRIPE_PRICES: {
        pro_monthly: 'price_xxxxx',
        pro_yearly: 'price_xxxxx',
        elite_monthly: 'price_xxxxx',
        elite_yearly: 'price_xxxxx'
    },
    APP_URL: 'https://sportsedgebet.com',
    // ... rest of config
};
```

### Step 4: Vercel Environment Variables

1. Go to your Vercel project → **Settings → Environment Variables**
2. Add these variables:

| Name | Value | Environment |
|------|-------|-------------|
| `SUPABASE_URL` | Your Supabase URL | All |
| `SUPABASE_SERVICE_KEY` | Your service_role key | All |
| `STRIPE_SECRET_KEY` | sk_live_xxxxx | All |
| `STRIPE_WEBHOOK_SECRET` | whsec_xxxxx | All |
| `STRIPE_PRICE_PRO_MONTHLY` | price_xxxxx | All |
| `STRIPE_PRICE_PRO_YEARLY` | price_xxxxx | All |
| `STRIPE_PRICE_ELITE_MONTHLY` | price_xxxxx | All |
| `STRIPE_PRICE_ELITE_YEARLY` | price_xxxxx | All |
| `APP_URL` | https://sportsedgebet.com | All |

### Step 5: Deploy

```bash
# Install dependencies (for API functions)
npm install

# Deploy to Vercel
git add .
git commit -m "Add backend integration"
git push
```

Vercel will automatically deploy on push.

---

## 📁 Project Structure

```
sportsedgebet/
├── api/                      # Vercel Serverless Functions
│   ├── create-checkout.js    # Creates Stripe checkout session
│   └── stripe-webhook.js     # Handles Stripe webhooks
├── scripts/
│   ├── config.js            # App configuration
│   ├── auth.js              # Authentication & Supabase client
│   └── main.js              # General UI scripts
├── styles/
│   └── main.css             # All styles
├── index.html               # Landing page
├── login.html               # Login page
├── signup.html              # Signup page
├── account.html             # User account dashboard
├── pricing.html             # Pricing page with Stripe
├── waitlist.html            # Waitlist page
├── dashboard.html           # Main app dashboard
├── supabase-schema.sql      # Database schema
├── package.json             # Dependencies
└── SETUP.md                 # This file
```

---

## 🔐 Database Schema

### Tables Created

| Table | Purpose |
|-------|---------|
| `profiles` | User profiles (extends Supabase auth) |
| `subscriptions` | User subscription status |
| `affiliates` | Affiliate program data |
| `referrals` | Referral tracking |
| `affiliate_payouts` | Payout history |
| `waitlist` | Waitlist signups |

### Row Level Security (RLS)

All tables have RLS enabled:
- Users can only read/write their own data
- Affiliates can see their referrals
- Service role key bypasses RLS (used in webhooks)

---

## 🧪 Testing

### Test Mode Setup

1. Use Stripe test keys (`pk_test_`, `sk_test_`)
2. Use test card: `4242 4242 4242 4242`
3. Any future date and any CVC

### Test the Flow

1. Sign up for a new account
2. Go to pricing page
3. Click "Start 7-Day Free Trial"
4. Complete checkout with test card
5. Check Supabase → `subscriptions` table for updated record

---

## 🚨 Troubleshooting

### "Invalid API Key" Error
- Make sure you're using the correct Supabase anon key in `config.js`
- Check that environment variables are set in Vercel

### Webhook Not Working
- Verify webhook URL is correct: `https://yourdomain.com/api/stripe-webhook`
- Check Stripe webhook logs for errors
- Ensure `STRIPE_WEBHOOK_SECRET` is correct

### User Not Created in Database
- Check Supabase → SQL Editor → Run: `SELECT * FROM auth.users`
- Verify the trigger exists: `SELECT * FROM pg_trigger WHERE tgname = 'on_auth_user_created'`

### CORS Errors
- Add your domain to Supabase → Authentication → URL Configuration

---

## 🔄 Going Live Checklist

- [ ] Switch to Stripe live keys
- [ ] Update `APP_URL` to production domain
- [ ] Set up production Stripe webhook
- [ ] Test complete signup → subscribe flow
- [ ] Set up email templates in Supabase (optional)
- [ ] Configure custom SMTP for emails (optional)

---

## 📞 Support

- Supabase Docs: https://supabase.com/docs
- Stripe Docs: https://stripe.com/docs
- Vercel Docs: https://vercel.com/docs

---

## 💡 Next Steps

1. **Add more features:**
   - Password reset page
   - Email verification handling
   - Account deletion

2. **Enhance security:**
   - Add rate limiting (use Upstash)
   - Set up monitoring (Vercel Analytics)

3. **Scale when needed:**
   - Upgrade Supabase when approaching limits
   - Add caching with Upstash Redis
   - Consider edge functions for global performance


