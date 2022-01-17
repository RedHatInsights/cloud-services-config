import sys
import subprocess

def main():
    edgeRcPath = sys.argv[1]
    branch = sys.argv[2]
    navlist = sys.argv[3:]
    domain = 'https://console.stage.redhat.com'
    if 'prod' in branch:
        domain = 'https://console.redhat.com'
    if 'beta' in branch:
        domain += '/beta'
    purgeAssets = ['fed-modules.json']
    for nav in navlist:
        purgeAssets.append(f'{nav}-navigation.json')
    purgeUrls = [f'{domain}/config/main.yml']
    for assetPath in purgeAssets:
        purgeUrls.append(f'{domain}/config/chrome/{assetPath}')
    for endpoint in purgeUrls:
        print(f'Purging endpoint cache: {endpoint}')
        try:
            subprocess.check_output(['akamai', 'purge', '--edgerc', edgeRcPath , 'invalidate', endpoint])
        except subprocess.CalledProcessError as e:
            print(e.output)
            sys.exit(1)

if __name__ == "__main__":
    main()
