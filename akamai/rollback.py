print(">>>>>>>>>>>>>>>>>>>>>>>> Rollback placeholder text! <<<<<<<<<<<<<<<<<<<<<<<<")
if len(sys.argv) > 2:
    rollback_version = sys.argv[2]
else:
    rollback_version = -1
print("We need to roll back to v{}".format(rollback_version))
