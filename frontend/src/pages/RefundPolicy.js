import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowLeft, RefreshCcw, Clock, Mail, CreditCard, AlertCircle, CheckCircle } from 'lucide-react';

const RefundPolicy = () => {
  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-white">
      {/* Navigation */}
      <nav className="sticky top-0 z-50 bg-white/80 backdrop-blur-md border-b border-slate-100">
        <div className="max-w-4xl mx-auto px-4 py-4 flex items-center justify-between">
          <Link to="/login" className="flex items-center gap-2 text-slate-600 hover:text-primary transition-colors">
            <ArrowLeft className="w-4 h-4" />
            <span className="text-sm">Back to Login</span>
          </Link>
          <img src="/logo-cognispace.png" alt="COGNISPACE" className="h-10 object-contain" />
        </div>
      </nav>

      {/* Content */}
      <main className="max-w-4xl mx-auto px-4 py-12">
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center">
              <RefreshCcw className="w-6 h-6 text-primary" />
            </div>
            <div>
              <h1 className="text-3xl font-serif text-slate-800">Refund & Cancellation Policy</h1>
              <p className="text-sm text-slate-500">Last updated: January 2026</p>
            </div>
          </div>
        </div>

        <div className="prose prose-slate max-w-none">
          
          {/* Introduction */}
          <section className="mb-8 p-6 bg-white rounded-xl border border-slate-200">
            <p className="text-slate-600 leading-relaxed">
              At <strong>COGNISPACE</strong> (operated by Vedic Wellness Solutions), we strive to ensure complete 
              satisfaction with our services. This policy outlines the terms and conditions for refunds and 
              cancellations related to subscription plans and services purchased through our platform.
            </p>
          </section>

          {/* Subscription Refunds */}
          <section className="mb-8">
            <div className="flex items-center gap-2 mb-4">
              <CreditCard className="w-5 h-5 text-primary" />
              <h2 className="text-xl font-semibold text-slate-800 m-0">1. Subscription Plans</h2>
            </div>
            <div className="bg-white rounded-xl border border-slate-200 p-6">
              <h3 className="text-lg font-medium text-slate-700 mb-3">Refund Eligibility</h3>
              <ul className="space-y-2 text-slate-600">
                <li className="flex items-start gap-2">
                  <CheckCircle className="w-4 h-4 text-green-500 mt-1 flex-shrink-0" />
                  <span><strong>Within 7 days:</strong> Full refund if no significant usage of premium features</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle className="w-4 h-4 text-green-500 mt-1 flex-shrink-0" />
                  <span><strong>7-15 days:</strong> Pro-rata refund based on unused period</span>
                </li>
                <li className="flex items-start gap-2">
                  <AlertCircle className="w-4 h-4 text-amber-500 mt-1 flex-shrink-0" />
                  <span><strong>After 15 days:</strong> No refund, but subscription can be cancelled for next billing cycle</span>
                </li>
              </ul>
            </div>
          </section>

          {/* Non-Refundable Items */}
          <section className="mb-8">
            <div className="flex items-center gap-2 mb-4">
              <AlertCircle className="w-5 h-5 text-amber-500" />
              <h2 className="text-xl font-semibold text-slate-800 m-0">2. Non-Refundable Items</h2>
            </div>
            <div className="bg-amber-50 rounded-xl border border-amber-200 p-6">
              <p className="text-slate-700 mb-3">The following are <strong>not eligible</strong> for refunds:</p>
              <ul className="space-y-2 text-slate-600">
                <li>• AI-generated reports and assessments already consumed</li>
                <li>• Partially used subscription periods beyond 15 days</li>
                <li>• Account setup and onboarding fees (if applicable)</li>
                <li>• Third-party integration fees (SMS, WhatsApp credits)</li>
                <li>• Subscriptions terminated due to policy violations</li>
              </ul>
            </div>
          </section>

          {/* Cancellation Process */}
          <section className="mb-8">
            <div className="flex items-center gap-2 mb-4">
              <Clock className="w-5 h-5 text-primary" />
              <h2 className="text-xl font-semibold text-slate-800 m-0">3. Cancellation Process</h2>
            </div>
            <div className="bg-white rounded-xl border border-slate-200 p-6">
              <h3 className="text-lg font-medium text-slate-700 mb-3">How to Cancel</h3>
              <ol className="space-y-3 text-slate-600">
                <li className="flex items-start gap-3">
                  <span className="w-6 h-6 rounded-full bg-primary/10 text-primary text-sm flex items-center justify-center flex-shrink-0">1</span>
                  <span>Log in to your COGNISPACE account</span>
                </li>
                <li className="flex items-start gap-3">
                  <span className="w-6 h-6 rounded-full bg-primary/10 text-primary text-sm flex items-center justify-center flex-shrink-0">2</span>
                  <span>Navigate to Settings → Subscription</span>
                </li>
                <li className="flex items-start gap-3">
                  <span className="w-6 h-6 rounded-full bg-primary/10 text-primary text-sm flex items-center justify-center flex-shrink-0">3</span>
                  <span>Click "Cancel Subscription" and follow the prompts</span>
                </li>
                <li className="flex items-start gap-3">
                  <span className="w-6 h-6 rounded-full bg-primary/10 text-primary text-sm flex items-center justify-center flex-shrink-0">4</span>
                  <span>Or email us at <strong>support@cognispace.in</strong> with your request</span>
                </li>
              </ol>
              <p className="mt-4 text-sm text-slate-500">
                Cancellation requests are processed within 2-3 business days.
              </p>
            </div>
          </section>

          {/* Refund Process */}
          <section className="mb-8">
            <div className="flex items-center gap-2 mb-4">
              <RefreshCcw className="w-5 h-5 text-primary" />
              <h2 className="text-xl font-semibold text-slate-800 m-0">4. Refund Process</h2>
            </div>
            <div className="bg-white rounded-xl border border-slate-200 p-6">
              <div className="grid md:grid-cols-2 gap-6">
                <div>
                  <h3 className="text-lg font-medium text-slate-700 mb-3">Processing Time</h3>
                  <ul className="space-y-2 text-slate-600 text-sm">
                    <li>• Request review: 2-3 business days</li>
                    <li>• Refund initiation: 3-5 business days</li>
                    <li>• Bank processing: 5-10 business days</li>
                  </ul>
                </div>
                <div>
                  <h3 className="text-lg font-medium text-slate-700 mb-3">Refund Method</h3>
                  <ul className="space-y-2 text-slate-600 text-sm">
                    <li>• Credit/Debit Card: Original payment method</li>
                    <li>• UPI: Original UPI ID</li>
                    <li>• Net Banking: Original bank account</li>
                  </ul>
                </div>
              </div>
            </div>
          </section>

          {/* Special Circumstances */}
          <section className="mb-8">
            <div className="flex items-center gap-2 mb-4">
              <CheckCircle className="w-5 h-5 text-green-500" />
              <h2 className="text-xl font-semibold text-slate-800 m-0">5. Special Circumstances</h2>
            </div>
            <div className="bg-green-50 rounded-xl border border-green-200 p-6">
              <p className="text-slate-700 mb-3">Full refunds may be granted in the following cases:</p>
              <ul className="space-y-2 text-slate-600">
                <li>• Duplicate payments or billing errors</li>
                <li>• Service unavailability exceeding 72 hours</li>
                <li>• Technical issues preventing platform access (verified by our team)</li>
                <li>• Unauthorized transactions (subject to verification)</li>
              </ul>
            </div>
          </section>

          {/* Contact */}
          <section className="mb-8">
            <div className="flex items-center gap-2 mb-4">
              <Mail className="w-5 h-5 text-primary" />
              <h2 className="text-xl font-semibold text-slate-800 m-0">6. Contact Us</h2>
            </div>
            <div className="bg-primary/5 rounded-xl border border-primary/20 p-6">
              <p className="text-slate-700 mb-4">
                For refund requests or queries regarding this policy, please contact us:
              </p>
              <div className="space-y-2 text-slate-600">
                <p><strong>Email:</strong> support@cognispace.in</p>
                <p><strong>Subject Line:</strong> Refund Request - [Your Account Email]</p>
                <p><strong>Response Time:</strong> Within 24-48 hours</p>
              </div>
              <p className="mt-4 text-sm text-slate-500">
                Please include your registered email, transaction ID, and reason for the refund request.
              </p>
            </div>
          </section>

          {/* Disclaimer */}
          <section className="p-4 bg-slate-100 rounded-lg text-sm text-slate-600">
            <p>
              <strong>Note:</strong> COGNISPACE reserves the right to modify this refund policy at any time. 
              Changes will be effective immediately upon posting on this page. Continued use of our services 
              after changes constitutes acceptance of the modified policy.
            </p>
          </section>

        </div>
      </main>

      {/* Footer */}
      <footer className="w-full py-6 px-4 border-t border-slate-200 bg-white mt-12">
        <div className="max-w-4xl mx-auto">
          <div className="flex flex-wrap justify-center gap-x-4 gap-y-2 text-xs text-slate-500 mb-4">
            <Link to="/about" className="hover:text-primary transition-colors">About</Link>
            <span className="text-slate-300">•</span>
            <Link to="/privacy-policy" className="hover:text-primary transition-colors">Privacy Policy</Link>
            <span className="text-slate-300">•</span>
            <Link to="/terms-conditions" className="hover:text-primary transition-colors">Terms & Conditions</Link>
            <span className="text-slate-300">•</span>
            <Link to="/clinical-disclaimer" className="hover:text-primary transition-colors">Clinical Disclaimer</Link>
            <span className="text-slate-300">•</span>
            <Link to="/contact" className="hover:text-primary transition-colors">Contact</Link>
          </div>
          <div className="text-center text-xs text-slate-400">
            <p>© 2026 COGNISPACE by Vedic Wellness Solutions</p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default RefundPolicy;
