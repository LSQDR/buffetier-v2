"""
SendGrid Email Integration
Sends order confirmations and notifications
"""

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from utils.secrets import get_secret
import os

def send_order_confirmation(to_email, user_name, order_details):
    """
    Send order confirmation email to customer
    
    Args:
        to_email: Customer email address
        user_name: Customer name
        order_details: Dict with order_id, total_amount, items, status
    
    Returns:
        bool: True if sent successfully
    """
    try:
        # Get API key from Secret Manager
        try:
            api_key = get_secret('sendgrid-api-key')
        except Exception as e:
            print(f"SendGrid API key not found: {e}")
            return False
        
        # Build email content
        items_html = ""
        for item in order_details.get('items', []):
            items_html += f"""
            <tr>
                <td style="padding: 10px; border-bottom: 1px solid #eee;">{item['name']}</td>
                <td style="padding: 10px; border-bottom: 1px solid #eee;">{item['quantity']}</td>
                <td style="padding: 10px; border-bottom: 1px solid #eee;">£{item['price']:.2f}</td>
            </tr>
            """
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                          color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: white; padding: 30px; border: 1px solid #ddd; }}
                .footer {{ background: #f8f9fa; padding: 20px; text-align: center; 
                          border-radius: 0 0 10px 10px; font-size: 12px; color: #666; }}
                table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                .total {{ font-size: 20px; font-weight: bold; color: #27ae60; text-align: right; 
                         padding: 15px; border-top: 2px solid #667eea; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🍽️ Order Confirmation</h1>
                </div>
                <div class="content">
                    <h2>Thank you, {user_name}!</h2>
                    <p>Your order has been received and is being prepared.</p>
                    
                    <p><strong>Order ID:</strong> #{order_details['order_id']}</p>
                    <p><strong>Status:</strong> <span style="color: #f39c12;">Pending</span></p>
                    
                    <h3>Order Details:</h3>
                    <table>
                        <thead>
                            <tr style="background: #f8f9fa;">
                                <th style="padding: 10px; text-align: left;">Item</th>
                                <th style="padding: 10px; text-align: left;">Quantity</th>
                                <th style="padding: 10px; text-align: left;">Price</th>
                            </tr>
                        </thead>
                        <tbody>
                            {items_html}
                        </tbody>
                    </table>
                    
                    <div class="total">
                        Total: £{order_details['total_amount']:.2f}
                    </div>
                    
                    <p style="margin-top: 30px;">You can track your order status in your 
                       <a href="http://localhost:8080/dashboard" style="color: #667eea;">dashboard</a>.</p>
                </div>
                <div class="footer">
                    <p>Buffetier Restaurant | Bournemouth, UK</p>
                    <p>This is an automated email. Please do not reply.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Create message
        message = Mail(
            from_email='lastsqdr@gmail.com', 
            to_emails=to_email,
            subject=f'Order Confirmation #{order_details["order_id"]}',
            html_content=html_content
        )
        
        # Send email
        sg = SendGridAPIClient(api_key)
        response = sg.send(message)
        
        print(f"✓ Email sent to {to_email}: {response.status_code}")
        return response.status_code == 202
        
    except Exception as e:
        print(f"✗ Email send failed: {e}")
        return False


def send_order_status_update(to_email, user_name, order_id, new_status):
    """Send order status update email"""
    try:
        print(f"=== EMAIL DEBUG ===")
        print(f"Attempting to send status update to: {to_email}")
        
        # Get API key from Secret Manager
        try:
            api_key = get_secret('sendgrid-api-key')
            print(f"✓ API key retrieved: {api_key[:10]}...")
        except Exception as e:
            print(f"✗ Failed to get API key: {e}")
            return False
        
        status_messages = {
            'pending': '⏳ Your order is pending confirmation',
            'confirmed': '✅ Your order has been confirmed',
            'preparing': '👨‍🍳 Your order is being prepared',
            'ready': '🎉 Your order is ready!',
            'completed': '✅ Your order has been completed',
            'cancelled': '❌ Your order has been cancelled'
        }
        
        status_message = status_messages.get(new_status, 'Your order status has been updated')
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <body style="font-family: Arial, sans-serif;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                           color: white; padding: 20px; border-radius: 10px 10px 0 0;">
                    <h1>Order Update</h1>
                </div>
                <div style="background: white; padding: 30px; border: 1px solid #ddd;">
                    <h2>Hi {user_name},</h2>
                    <p style="font-size: 18px;">{status_message}</p>
                    <p><strong>Order ID:</strong> #{order_id}</p>
                    <p><strong>New Status:</strong> <span style="color: #667eea; font-weight: bold;">
                       {new_status.upper()}</span></p>
                    <p style="margin-top: 30px;">
                        <a href="http://localhost:8080/dashboard" 
                           style="background: #667eea; color: white; padding: 12px 24px; 
                                  text-decoration: none; border-radius: 5px; display: inline-block;">
                            View Order Details
                        </a>
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        from_email_address = 'lastsqdr@gmail.com'  
        
        print(f"From: {from_email_address}")
        print(f"To: {to_email}")
        print(f"Subject: Order #{order_id} - Status Update")
        
        message = Mail(
            from_email=from_email_address,
            to_emails=to_email,
            subject=f'Order #{order_id} - Status Update',
            html_content=html_content
        )
        
        sg = SendGridAPIClient(api_key)
        response = sg.send(message)
        
        print(f"✓ Email sent! Status code: {response.status_code}")
        return response.status_code == 202
        
    except Exception as e:
        print(f"✗ Email send failed: {e}")
        import traceback
        traceback.print_exc()
        return False
