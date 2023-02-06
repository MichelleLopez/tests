import dns.resolver

if __name__ == '__main__':
    answers = dns.resolver.query('gmail.com', 'MX')
    for rdata in answers:
        print('Hosts %s has preference %s' % (rdata.exchange, rdata.preference))

