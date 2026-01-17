// Vercel Serverless Function - Stripe Webhook Handler
// Handles subscription events from Stripe

const stripe = require('stripe')(process.env.STRIPE_SECRET_KEY);
const { createClient } = require('@supabase/supabase-js');

const supabase = createClient(
    process.env.SUPABASE_URL,
    process.env.SUPABASE_SERVICE_KEY // Service key for admin access
);

// Disable body parsing to get raw body for signature verification
export const config = {
    api: {
        bodyParser: false,
    },
};

async function buffer(readable) {
    const chunks = [];
    for await (const chunk of readable) {
        chunks.push(typeof chunk === 'string' ? Buffer.from(chunk) : chunk);
    }
    return Buffer.concat(chunks);
}

export default async function handler(req, res) {
    if (req.method !== 'POST') {
        return res.status(405).json({ error: 'Method not allowed' });
    }

    const buf = await buffer(req);
    const sig = req.headers['stripe-signature'];

    let event;

    try {
        event = stripe.webhooks.constructEvent(
            buf,
            sig,
            process.env.STRIPE_WEBHOOK_SECRET
        );
    } catch (err) {
        console.error('Webhook signature verification failed:', err.message);
        return res.status(400).send(`Webhook Error: ${err.message}`);
    }

    // Handle the event
    try {
        switch (event.type) {
            case 'checkout.session.completed':
                await handleCheckoutComplete(event.data.object);
                break;

            case 'customer.subscription.created':
            case 'customer.subscription.updated':
                await handleSubscriptionUpdate(event.data.object);
                break;

            case 'customer.subscription.deleted':
                await handleSubscriptionDeleted(event.data.object);
                break;

            case 'invoice.paid':
                await handleInvoicePaid(event.data.object);
                break;

            case 'invoice.payment_failed':
                await handlePaymentFailed(event.data.object);
                break;

            default:
                console.log(`Unhandled event type: ${event.type}`);
        }

        return res.status(200).json({ received: true });
    } catch (error) {
        console.error('Webhook handler error:', error);
        return res.status(500).json({ error: error.message });
    }
}

// Handle successful checkout
async function handleCheckoutComplete(session) {
    const userId = session.metadata?.userId;
    if (!userId) {
        console.error('No userId in checkout session metadata');
        return;
    }

    // Update user's subscription in database
    const { error } = await supabase
        .from('subscriptions')
        .update({
            stripe_customer_id: session.customer,
            stripe_subscription_id: session.subscription,
            status: 'active',
        })
        .eq('user_id', userId);

    if (error) {
        console.error('Error updating subscription:', error);
    }

    // Track referral conversion if exists
    await trackReferralConversion(userId);
}

// Handle subscription updates
async function handleSubscriptionUpdate(subscription) {
    const userId = subscription.metadata?.userId;
    
    // Determine plan from price ID
    const priceId = subscription.items.data[0]?.price.id;
    const planId = getPlanFromPriceId(priceId);

    const updateData = {
        status: subscription.status,
        plan_id: planId,
        current_period_start: new Date(subscription.current_period_start * 1000).toISOString(),
        current_period_end: new Date(subscription.current_period_end * 1000).toISOString(),
        cancel_at_period_end: subscription.cancel_at_period_end,
    };

    // Update by stripe_subscription_id or userId
    const { error } = await supabase
        .from('subscriptions')
        .update(updateData)
        .eq('stripe_subscription_id', subscription.id);

    if (error) {
        console.error('Error updating subscription:', error);
    }
}

// Handle subscription cancellation
async function handleSubscriptionDeleted(subscription) {
    const { error } = await supabase
        .from('subscriptions')
        .update({
            status: 'canceled',
            plan_id: 'free',
        })
        .eq('stripe_subscription_id', subscription.id);

    if (error) {
        console.error('Error handling subscription deletion:', error);
    }
}

// Handle successful invoice payment (for recurring billing)
async function handleInvoicePaid(invoice) {
    if (!invoice.subscription) return;

    // Calculate affiliate commission if applicable
    const subscription = await stripe.subscriptions.retrieve(invoice.subscription);
    const userId = subscription.metadata?.userId;
    
    if (userId) {
        await processAffiliateCommission(userId, invoice.amount_paid / 100);
    }
}

// Handle failed payment
async function handlePaymentFailed(invoice) {
    if (!invoice.subscription) return;

    const { error } = await supabase
        .from('subscriptions')
        .update({ status: 'past_due' })
        .eq('stripe_subscription_id', invoice.subscription);

    if (error) {
        console.error('Error updating subscription status:', error);
    }
}

// Track referral conversion
async function trackReferralConversion(userId) {
    const { data: referral } = await supabase
        .from('referrals')
        .select('*, affiliates(*)')
        .eq('referred_user_id', userId)
        .single();

    if (referral && referral.status === 'pending') {
        await supabase
            .from('referrals')
            .update({
                status: 'converted',
                converted_at: new Date().toISOString(),
            })
            .eq('id', referral.id);
    }
}

// Process affiliate commission
async function processAffiliateCommission(userId, amount) {
    const { data: referral } = await supabase
        .from('referrals')
        .select('*, affiliates(*)')
        .eq('referred_user_id', userId)
        .eq('status', 'converted')
        .single();

    if (referral && referral.affiliates) {
        const commission = amount * (referral.affiliates.commission_rate / 100);
        
        // Update affiliate earnings
        await supabase
            .from('affiliates')
            .update({
                pending_earnings: supabase.sql`pending_earnings + ${commission}`,
                total_earnings: supabase.sql`total_earnings + ${commission}`,
            })
            .eq('id', referral.affiliate_id);

        // Update referral commission
        await supabase
            .from('referrals')
            .update({
                commission_earned: supabase.sql`commission_earned + ${commission}`,
            })
            .eq('id', referral.id);
    }
}

// Map Stripe price IDs to plan IDs
function getPlanFromPriceId(priceId) {
    const priceMap = {
        [process.env.STRIPE_PRICE_PRO_MONTHLY]: 'pro',
        [process.env.STRIPE_PRICE_PRO_YEARLY]: 'pro',
        [process.env.STRIPE_PRICE_ELITE_MONTHLY]: 'elite',
        [process.env.STRIPE_PRICE_ELITE_YEARLY]: 'elite',
    };
    return priceMap[priceId] || 'free';
}


