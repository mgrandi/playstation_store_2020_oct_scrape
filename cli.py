#!/usr/bin/env python3
from playstation_store_2020_oct_scrape import main

# this script has been separated out so all of the code that WAS here is now in a
# importable module, so we can use it with pex
# this file now just imports that and calls the main() method
if __name__ == "__main__":
    main.main()
