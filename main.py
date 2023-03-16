import requests


def run_query(query):
    response = requests.post('https://api.tarkov.dev/graphql', json={'query': query})
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception("Query failed to run by returning code of {}. {}".format(response.status_code, query))


def price_check_failed(name):
    while True:
        print(f"{name} price check failed, please manually enter a value.")
        price = input("--> ")
        try:
            price = int(price)
            if price > 0:
                break
            else:
                print(f"'{price}' is not a number over 0, try again.")
        except ValueError:
            print(f"'{price}' is not a whole number, try again.")
    return price


def flea_price_check(result_name, position: int, name: str) -> int:
    try:
        price = result_name['data']['items'][position]['avg24hPrice']
        return price
    except KeyError:
        price_check_failed(name)


if __name__ == '__main__':
    input("Welcome to Tarkov BTC Farm Profit Calculator, press enter to begin.")

    print("\nInclude fuel costs in calculation? (y or n)")
    use_fuel = input("--> ")
    use_fuel = use_fuel.lower().strip()
    hours_per_fuel = 21.0525  # This is the base amount of time one metal fuel tank lasts in the generator

    if use_fuel == "y":
        print("\nCalculate solar power -50% fuel consumption? (y or n)")
        solar = input("--> ")
        if solar.lower().strip() == 'y':
            hours_per_fuel *= 2

        # Calculate fuel time increase based on hideout management skill
        print("\nHideout management level? (1 - 51)")
        while True:
            hm_level = input("--> ")
            try:
                hm_level = int(hm_level)
                if 0 < hm_level <= 51:
                    hm_fuel_multiplier = 1 + (0.01 * (hm_level * 0.5))
                    break
                else:
                    print(f"'{hm_level}' is not a number between 1 and 51")
            except ValueError:
                print(f"'{hm_level}' is not a whole number, try again")

        # Adding fuel increase percentage to fuel hours
        if hm_fuel_multiplier != 0:
            hours_per_fuel *= hm_fuel_multiplier

        # Define Fuel Price (i.e. cost per x time spent mining)
        fuel_query = """
        {
            itemsByName(name: "Metal Fuel Tank") {
                avg24hPrice
                basePrice
            }
        }
        """

        try:
            fuel_result = run_query(fuel_query)
            fuel_flea_price = fuel_result['data']['itemsByName'][0]['avg24hPrice']
            fuel_trader_price = fuel_result['data']['itemsByName'][0]['basePrice']
            if fuel_flea_price > fuel_trader_price:
                fuel_price = fuel_trader_price
            else:
                fuel_price = fuel_flea_price
        except KeyError:
            while True:
                fuel_price = price_check_failed("Metal Fuel Tank")
    else:
        fuel_price = 0

    print("\nInclude cost of building/upgrading bitcoin farm? (y or n)")
    include_btc_cost = input("--> ")
    include_btc_cost = include_btc_cost.lower().strip()

    needed_upgrades = []
    solar_required = False
    desired_btc_level = 0
    cpu_fan = "CPU Fan"
    if include_btc_cost == "y":
        print("\nEnter current bitcoin farm level (0 to 3)")
        while True:
            current_btc_level = input("--> ")
            try:
                current_btc_level = int(current_btc_level)
                if 0 <= current_btc_level <= 3:
                    break
                else:
                    print(f"'{current_btc_level}' is not a number between 0 and 3, try again.")
            except ValueError:
                print(f"'{current_btc_level}' is not a whole number, try again.")

        if current_btc_level < 3:
            print(f"\nEnter desired bitcoin farm level ({current_btc_level + 1} to 3) (blank = no upgrade)")
            while True:
                desired_btc_level = input("--> ")
                if desired_btc_level:
                    try:
                        desired_btc_level = int(desired_btc_level)
                        if current_btc_level <= desired_btc_level <= 3:
                            break
                        else:
                            print(f"'{desired_btc_level}' is invalid, try again.")
                    except ValueError:
                        print(f"'{desired_btc_level}' is not a whole number, try again.")
                else:
                    desired_btc_level = current_btc_level
            if desired_btc_level != current_btc_level:
                needed_upgrades = list(range(current_btc_level + 1, desired_btc_level + 1))
        else:
            desired_btc_level = 3
        if current_btc_level <= 2 and desired_btc_level == 3:
            print("\nInclude solar power build costs in calculation? (y or n) (Required for Bitcoin Farm Level 3)")
            solar = input("--> ")
            if solar.lower().strip() == 'y':
                solar_required = True

    # Define how much bitcoin sells to Therapist for
    btc_query = """
    {
        itemsByName(name: "BTC") {
            sellFor {
              price
            }
        }
    }
    """

    try:
        btc_result = run_query(btc_query)
        btc_price = btc_result['data']['itemsByName'][0]['sellFor'][0]['price']  # 4 prices given, first one is therapist
    except KeyError:
        btc_price = price_check_failed("BTC")

    print("\n--- Main Prices ---")
    print(f"₽ {btc_price:,} - Bitcoin")

    # Define the 24-hour price of Graphics Cards on the flea market
    gpu_query = """
    {
        itemsByName(name: "Graphics card") {
            avg24hPrice
        }
    }
    """

    try:
        gpu_result = run_query(gpu_query)
        gpu_price = gpu_result['data']['itemsByName'][0]['avg24hPrice']
    except KeyError:
        gpu_price = price_check_failed("Graphics card")

    print(f"₽ {gpu_price:,} - Graphics Card")

    if use_fuel == "y":
        print(f"₽ {fuel_price:,} - Metal Fuel Tank")
        print(f"{round(hours_per_fuel, 2)} hours per Metal Fuel Tank")

    if include_btc_cost == "y":
        total_btc_build_price = 0

        if 1 in needed_upgrades:
            btc1_query = """
            {
                items(names: ["T-Shaped plug", "VPX Flash Storage Module", "Power cord", "Power supply unit", "CPU fan"]) 
                {
                    avg24hPrice
                }
            }
            """

            btc1_result = run_query(btc1_query)

            cpu_fan_price = (flea_price_check(btc1_result, 0, cpu_fan) * 15)
            psu_price = (flea_price_check(btc1_result, 1, "Power supply unit") * 10)
            t_plug_price = (flea_price_check(btc1_result, 2, "T-Shaped plug") * 5)
            power_cord_price = (flea_price_check(btc1_result, 3, "Power cord") * 10)
            vpx_price = flea_price_check(btc1_result, 4, "VPX Flash Storage Module")

            btc1_build_price = cpu_fan_price + psu_price + t_plug_price + power_cord_price + vpx_price

            total_btc_build_price += btc1_build_price

            print("\n--- Bitcoin Farm Level 1 ---")
            print(f"₽ {cpu_fan_price:,} - 15x CPU fan")
            print(f"₽ {psu_price:,} - 10x Power supply unit")
            print(f"₽ {t_plug_price:,} - 5x T-Shaped plug")
            print(f"₽ {power_cord_price:,} - 10x Power cord")
            print(f"₽ {vpx_price:,} - 1x VPX Flash Storage Module")
            print(f"\n₽ {btc1_build_price:,} - Total cost of Bitcoin Farm Level 1")

        if 2 in needed_upgrades:
            btc2_query = """
            {
                items(names: ["CPU fan", "Power supply unit", "Printed circuit board", "Phase control relay", 
                "Military power filter"]) 
                {
                    avg24hPrice
                }
            }
            """

            btc2_result = run_query(btc2_query)

            cpu_fan_price = flea_price_check(btc2_result, 0, cpu_fan) * 15
            psu_price = flea_price_check(btc2_result, 1, "Power supply unit") * 10
            pcb_price = flea_price_check(btc2_result, 2, "Printed circuit board") * 15
            power_filter_price = flea_price_check(btc2_result, 3, "Military power filter") * 2
            relay_price = flea_price_check(btc2_result, 4, "Phase control relay") * 5

            btc2_build_price = cpu_fan_price + psu_price + pcb_price + power_filter_price + relay_price

            total_btc_build_price += btc2_build_price

            print("\n--- Bitcoin Farm Level 2 ---")
            print(f"₽ {cpu_fan_price:,} - 15x CPU fan")
            print(f"₽ {psu_price:,} - 10x Power supply unit")
            print(f"₽ {pcb_price:,} - 15x Printed circuit board")
            print(f"₽ {power_filter_price:,} - 2x Military power filter")
            print(f"₽ {relay_price:,} - 5x Phase control relay")

            print(f"\n₽ {btc2_build_price:,} - Total cost of Bitcoin Farm Level 2")

        if 3 in needed_upgrades:
            btc3_query = """
            {
                items(names: ["CPU fan", "Silicone tube", "Electric motor", "Pressure gauge", 
                "6-STEN-140-M military battery"]) 
                {
                    avg24hPrice
                }
            }
            """

            btc3_result = run_query(btc3_query)

            cpu_fan_price = (flea_price_check(btc3_result, 0, cpu_fan) * 25)
            battery_price = flea_price_check(btc3_result, 1, "6-STEN-140-M military battery")
            motor_price = (flea_price_check(btc3_result, 2, "Electric motor") * 10)
            gauge_price = (flea_price_check(btc3_result, 3, "Pressure gauge") * 10)
            tube_price = (flea_price_check(btc3_result, 4, "Silicone tube") * 15)

            btc3_build_price = cpu_fan_price + battery_price + motor_price + gauge_price + tube_price

            print("\n--- Bitcoin Farm Level 3 ---")
            print(f"₽ {cpu_fan_price:,} - 25x CPU fan")
            print(f"₽ {battery_price:,} - 1x 6-STEN-140-M military battery")
            print(f"₽ {motor_price:,} - 10x Electric motor")
            print(f"₽ {gauge_price:,} - 10x Pressure gauge")
            print(f"₽ {tube_price:,} - 15x Silicon tube")

            print(f"\n₽ {btc3_build_price:,} - Total cost of Bitcoin Farm Level 3")

            if solar_required:
                solar_query = """
                        {
                            items(names: ["Phased array element", "Working LCD", "Military cable", "Military power filter"]) 
                            {
                                avg24hPrice
                            }
                        }
                        """

                solar_result = run_query(solar_query)

                phased_array_price = (flea_price_check(solar_result, 0, "Phased array element") * 4)
                working_lcd_price = (flea_price_check(solar_result, 0, "Working LCD") * 3)
                military_cable_price = (flea_price_check(solar_result, 0, "Military cable") * 10)
                power_filter_price = (flea_price_check(solar_result, 0, "Military Power Filter") * 10)
                euros_price = (120 * 75000)

                solar_build_price = phased_array_price + working_lcd_price + military_cable_price + power_filter_price + euros_price

                print("\n--- Solar Power ---")
                print(f"₽ {phased_array_price:,} - 4x Phased array element")
                print(f"₽ {working_lcd_price:,} - 3x Working LCD")
                print(f"₽ {military_cable_price:,} - 10x Military cable")
                print(f"₽ {power_filter_price:,} - 10x Military Power Filter")
                print(f"₽ {euros_price:,} - 75000x Euros")

                print(f"\n₽ {solar_build_price:,} - Total cost of Solar Power")

                btc3_build_price += solar_build_price

                print(f"\n₽ {btc3_build_price:,} - Total cost of Bitcoin Farm Level 3 + Solar Power")

            total_btc_build_price += btc3_build_price

        print("\n--- Bitcoin Farm Total ---")
        print(f"₽ {total_btc_build_price:,} - Total cost of upgrading Bitcoin Farm")
    else:
        total_btc_build_price = 0

    # Define currently owned GPUs
    print("\nEnter amount of GPUs currently owned (blank = 0)")
    while True:
        current_gpu = input("--> ")
        if current_gpu:
            try:
                current_gpu = int(current_gpu)
                if 0 <= current_gpu <= 50:
                    break
                else:
                    print(f"'{current_gpu}' is not a number between 0 and 50, try again")
            except ValueError:
                print(f"'{current_gpu}' is not a whole number, try again")
        else:
            current_gpu = int(0)
            break

    # Define the amount of GPUs to be purchased
    desired_gpu = int(0)
    if current_gpu < 50:
        print("\nEnter amount of (additional) GPUs to be purchased (blank = 0)")
        gpu_slots = 50
        while True:
            if include_btc_cost == "y":
                if desired_btc_level == 1:
                    gpu_slots = 10 - current_gpu
                    print(f"Given your desired BTC farm level, you must enter a value between 0 and {gpu_slots}.")
                elif desired_btc_level == 2:
                    gpu_slots = 25 - current_gpu
                    print(f"Given your desired BTC farm level, you must enter a value between 0 and {gpu_slots}.")
                elif desired_btc_level == 3:
                    gpu_slots = 50 - current_gpu
                    print(f"Given your desired BTC farm level, you must enter a value between 0 and {gpu_slots}.")
            desired_gpu = input("--> ")
            if desired_gpu:
                try:
                    desired_gpu = int(desired_gpu)
                    if 0 <= desired_gpu <= gpu_slots:
                        break
                    else:
                        print(f"'{desired_gpu}' is not a number between 0 and {gpu_slots}, try again")
                except ValueError:
                    print(f"'{desired_gpu}' is not a whole number, try again")
            else:
                desired_gpu = int(0)
                break

    # BTC farm calculation from wiki
    gpu_count = desired_gpu + current_gpu
    hour_per_btc = 145000 / (1 + (gpu_count - 1) * 0.041225) / 3600

    print("\n--- Timing ---")
    print(f"{round(hour_per_btc, 2)} hours to mine one BTC @ {btc_price:,} ₽")

    btc_per_hour = btc_price / hour_per_btc
    total_gpu_price = desired_gpu * gpu_price
    grand_total = total_gpu_price + total_btc_build_price

    if use_fuel == 'y':
        print(f"{round(hours_per_fuel, 2)} hours per Metal Fuel Tank @ {fuel_price:,} ₽")
        fuel_per_hour = fuel_price / hours_per_fuel
        profit_per_hour = btc_per_hour - fuel_per_hour
        payback_hours = grand_total / profit_per_hour
    else:
        payback_hours = grand_total / btc_per_hour

    print("\n--- Sub Total ---")
    print(f"GPUs Total: {total_gpu_price:,} ₽")
    print(f"Bitcoin Farm Total: {total_btc_build_price:,} ₽")

    print("\n--- Grand Total ---")
    print(f"{round(payback_hours / 24, 2)} days to pay back {desired_gpu} GPUs and hideout items costing a total of {grand_total:,} ₽")
    if payback_hours < 0:
        print("This number seems to be negative, you'll probably never make your money back.")
