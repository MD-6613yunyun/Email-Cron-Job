#!/bin/bash

# path location of sendmail 
SENDMAIL_BIN='/usr/sbin/sendmail'
FROM_MAIL_ADDRESS='yunyun.mdmm@gmail.com'
FROM_MAIL_DISLAY='MUDON MAUNG MAUNG'
RECIPIENT_ADDRESSES='maeupyaesone@gmail.com,yunyun.mdmm@gmail.com'

MAIL_CMD="$SENDMAIL_BIN -f $FROM_MAIL_ADDRESS -F \"$FROM_MAIL_DISLAY\" $RECIPIENT_ADDRESSES"
(echo "Subject: Record Creations Daily Report";echo -e "MIME-Version: 1.0\nContent-Type: text/html;\n" &&  cat /path/to/the/file.html ) | eval $MAIL_CMD
