import email
import logging
import smtplib
import socket
import sys
import time
from contextlib import contextmanager
from smtplib import SMTPResponseException

# Logging setup.
logging.basicConfig(filename='cliente.log', format='%(asctime)s - %(levelname)s: %(message)s',
                    datefmt='%d/%m/%Y %I:%M:%S %p', level=logging.DEBUG)


@contextmanager
def sender(SERVER, PORT):
    try:
        print('Starting server connection... Please wait.')
        logging.info('Starting server connection... Please wait.')
        # Connecting to SERVER
        smtp = smtplib.SMTP(SERVER, PORT)
        print('Connection succeded.')
        logging.info('Connection succesful.')
        yield smtp
    except socket.timeout:
        print('Timeout occurred while connecting to the server.')
        logging.critical('Timeout occurred while connecting to the server.')
    except smtplib.SMTPConnectError:
        print('Connection to server error. Aborting')
        logging.critical('Connection to server error. Aborting.')
    except smtplib.SMTPServerDisconnected:
        print('The connection has been terminated unexpectedly. Server disconnected.')
        logging.critical('The connection has been terminated unexpectedly. Server disconnected.')
    except smtplib.SMTPResponseException:
        print(SMTPResponseException.smtp_code + ' - ' + SMTPResponseException.smtp_error)
        logging.critical(SMTPResponseException.smtp_code + ' - ' + SMTPResponseException.smtp_error)
    except smtplib.SMTPException as err:
        print('Generic SMTP Exception.', err)
        logging.critical('SMTP Exception. - ' + str(err))
    except Exception as err:
        print('You messed it up, check the code. (Hint, probably server and port are not written correctly)', err)
        logging.critical(
            'You messed it up, check the code. (Hint, probably server and port are not written correctly) - ' + str(
                err))
    finally:
        # Once finished, close connection and quit gracefully.
        try:
            q = smtp.quit()
            print('Connection succesfully terminated.', q)
            logging.info('Connection succesfully terminated. - ' + str(q))
        except UnboundLocalError as err:
            print('"smtp" variable is empty, exception raised.', err)
            logging.error('"smtp" variable is empty, exception raised. - ' + str(err))


# Open files
mails = open('ALL.txt', 'r')
notSent = open('NotSent.txt', 'a')

# Variables setup
SMTP_SERVER = 'mail.sisap.com'  # Client address
SMTP_PORT = 25
SMTP_FROM = '"FROM" <jorge.martinez@sisap.com>'

try:
    with sender(SMTP_SERVER, SMTP_PORT) as smtp:
        for mail in mails:
            SMTP_TO = mail

            # Mail setup, variable replace
            user = mail[0:mail.index('@')]
            msg = open('Cliente.txt', 'r')
            final_msg = ''
            while True:
                ch = msg.read(1)
                if not ch:
                    break
                if ch != '%':
                    final_msg += ch
                else:
                    final_msg += user
                    while ch != '%':
                        ch = msg.read(1)
            message = final_msg  # Final email to send.

            # Construct the email with MIME
            msg = email.MIMEMultipart.MIMEMultipart('alternative')
            bodyHTML = email.MIMEText.MIMEText(message, 'html')
            msg['Subject'] = 'Formacion Profesional y Personal'
            msg['From'] = SMTP_FROM
            msg['To'] = SMTP_TO
            msg.attach(bodyHTML)
            try:
                # Sending email
                smtp.sendmail(SMTP_FROM, [SMTP_TO], msg.as_string())
                print(mail[:-1] + ' sent succesfully.')
                logging.info(mail[:-1] + ' sent succesfully.')
            except smtplib.SMTPHeloError:
                notSent.write(str(mail))
                print('The server did not reply properly to the HELO greeting.')
                logging.critical('The server did not reply properly to the HELO greeting.')
            except smtplib.SMTPRecipientsRefused:
                notSent.write(str(mail))
                print('The recipient ' + str(
                    mail).rstrip() + ' was refused. Nobody got the mail. Adding to the NotSent.txt file.')
                logging.critical('The recipient ' + str(
                    mail).rstrip() + ' was refused. Nobody got the mail. Adding to the NotSent.txt file.')
            except smtplib.SMTPSenderRefused:
                notSent.write(str(mail))
                print('The server did not accept the from_addr.')
                logging.critical('The server did not accept the from_addr.')
            except:
                notSent.write(str(mail))
                print('Unexpected error: ', sys.exc_info()[0])
                logging.error('Unexpected error: ' + str(sys.exc_info()[0]))
                raise

            # 5 seconds delay - TESTING FEATURE
            time.sleep(5)

        # All mails sent, close the files
        mails.close()
        notSent.close()

except RuntimeError as err:
    print('Unexpected error: ', err)
    logging.error('Unexpected error: ' + str(err))
