// Vercel Serverless Function - Create Stripe Checkout Session
// This runs on Vercel's servers (FREE tier includes 100K invocations/month)

const stripe = require('stripe')(process.env.STRIPE_SECRET_KEY);

const PRICES = {
    pro_monthly: process.env.STRIPE_PRICE_PRO_MONTHLY,
    pro_yearly: process.env.STRIPE_PRICE_PRO_YEARLY,
    elite_monthly: process.env.STRIPE_PRICE_ELITE_MONTHLY,
    elite_yearly: process.env.STRIPE_PRICE_ELITE_YEARLY,
};

export default async function handler(req, res) {
    // Enable CORS
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

    if (req.method === 'OPTIONS') {
        return res.status(200).end();
    }

    if (req.method !== 'POST') {
        return res.status(405).json({ error: 'Method not allowed' });
    }

    try {
        const { priceId, userId, userEmail, successUrl, cancelUrl } = req.body;

        if (!priceId || !PRICES[priceId]) {
            return res.status(400).json({ error: 'Invalid price ID' });
        }

        // Create Checkout Session
        const session = await stripe.checkout.sessions.create({
            mode: 'subscription',
            payment_method_types: ['card'],
            line_items: [
                {
                    price: PRICES[priceId],
                    quantity: 1,
                },
            ],
            success_url: successUrl || `${process.env.APP_URL}/account.html?success=true`,
            cancel_url: cancelUrl || `${process.env.APP_URL}/pricing.html?canceled=true`,
            customer_email: userEmail,
            metadata: {
                userId: userId,
            },
            subscription_data: {
                metadata: {
                    userId: userId,
                },
                trial_period_days: 7, // 7-day free trial
            },
            allow_promotion_codes: true,
        });

        return res.status(200).json({ 
            sessionId: session.id,
            url: session.url 
        });
    } catch (error) {
        console.error('Stripe error:', error);
        return res.status(500).json({ error: error.message });
    }
}


