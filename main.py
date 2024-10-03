# IMPORTS
from flask import Flask, render_template, request, session
from flask_bootstrap import Bootstrap5
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Length, Regexp
import requests
from datetime import datetime
import os
import re


## -----------------------------------GOOGLE PLACES API---------------------------------##

#CONSTANTS
# Get the API key from the environment variable
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')

## ----------------------------------FLASK SETUP---------------------------------------##
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
Bootstrap5(app)


## ------------------------------WTforms setup---------------------------------- ##
class SearchForm(FlaskForm):
    apartment_name = StringField("Apartment Name", validators=[DataRequired()])
    zip_code = StringField("Zip Code", validators=[DataRequired(), Length(min=5, max=5, message="Zip code must be exactly 5 digits.")])
    submit = SubmitField("Search")


## ------------------------------------FLASK WEB ROUTING--------------------------------------------##

@app.route("/", methods=["GET", "POST"])
def home():
    form = SearchForm()
    overall_rating = None
    filtered_reviews = []
    apartment_details = None # Initialize apartment details
    search_performed = False  # Flag to track whether a search was made
    reviews_count = 0
    review_dates = []

    # Use Google Places API to search for apartment
    if form.validate_on_submit():
        search_performed = True  # Set flag to true once submit button clicked
        place_name = form.apartment_name.data
        zip_code = form.zip_code.data

        # Call function to use API
        overall_rating, reviews_count, filtered_reviews, review_dates, apartment_details = main(place_name, zip_code, GOOGLE_API_KEY)


        # Ensure reviews_count is not None
        if reviews_count is None:
            reviews_count = 0  # Default to 0 if no reviews_count is available

        # Ensure that apartment_details is a dictionary before using .get()
        if apartment_details is None:
            apartment_details = {'name': 'N/A', 'formatted_address': 'N/A', 'url': 'N/A', 'user_ratings_total': 0}

        # Pair each review with its corresponding date
        reviews_with_dates = list(zip(filtered_reviews, review_dates))

        # Pass the session value to the template
        roaches_review_count = session.get('roaches_review_count', 'N/A')

        # Check if the request is an AJAX request using FLASK 'request' object
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # Return only the relevant HTML for reviews
            return render_template(
                'reviews_partial.html',
                overall_rating=overall_rating,
                reviews=filtered_reviews,
                reviews_with_dates=reviews_with_dates,
                search_performed=search_performed,
                name=apartment_details.get('name'),
                formatted_address=apartment_details.get('formatted_address'),
                url=apartment_details.get('url'),
                reviews_count=reviews_count
            )

        # if it's not an AJAX request, return the full page
        return render_template(
            "index.html",
            form=form,
            overall_rating=overall_rating,
            reviews=filtered_reviews,
            reviews_with_dates=reviews_with_dates,
            search_performed=search_performed,
            name=apartment_details.get('name'),
            formatted_address=apartment_details.get('formatted_address'),
            url=apartment_details.get('url'),
            reviews_count=reviews_count
        )

    # Handle GET request, return full page
    return render_template("index.html", form=form)

# -------------------------------GOOGLE PLACES API FUNCTION TO GET PLACE ID---------------------------#
def get_place_id(place_name, zip_code, GOOGLE_API_KEY):
    # Google Places text search API URL if name and zip code given
    url = f"https://maps.googleapis.com/maps/api/place/findplacefromtext/json?inputtype=textquery&fields=place_id&input={place_name}+{zip_code}&key={GOOGLE_API_KEY}"
    # Send a GET request to the API
    response = requests.get(url)
    # Parse response to JSON
    data = response.json()

    # Check if there are candidates in the response
    if 'candidates' in data and len(data['candidates']) > 0:
        # Get the first candidate's place_id
        place_id = data['candidates'][0]['place_id']
        return place_id

    else:
        return None #Return None if no place is found

# -------------------------------GOOGLE PLACES API FUNCTION TO GET APARTMENT REVIEWS---------------------------#

def get_place_reviews_and_rating(place_id, GOOGLE_API_KEY):
    url = f"https://maps.googleapis.com/maps/api/place/details/json?placeid={place_id}&fields=rating,reviews&key={GOOGLE_API_KEY}"
    # Send a GET request to the API
    response = requests.get(url)
    data = response.json()

    # Check if there are reviews
    if 'result' in data:
        result = data['result']
        # Get overall rating if it exists
        overall_rating = result.get('rating', 'No rating available')
        # Get reviews if they exists
        reviews = result.get('reviews', [])



        # Extract date from each review
        review_dates = []
        for review in reviews:
            time = review.get('time')
            # Convert to readable date
            review_date = datetime.utcfromtimestamp(time).strftime('%Y-%m-%d')
            review_dates.append(review_date)



        return overall_rating, reviews, review_dates
    else:
        return None, 0, [] # Return None, 0 and an empty list if no result is found



#----------------------------------FILTER REVIEWS WITH KEYWORDS---------------------------------------#
def filter_reviews(reviews, keywords):
    # Create a list to store filtered reviews
    filtered_reviews = []
    # Compile keywords into regex patterns
    keyword_patterns = [re.compile(r'\b' + re.escape(keyword) + r'\b', re.IGNORECASE) for keyword in keywords]

    # Iterate over each review to check if it contains any of the keywords
    for review in reviews:
        for pattern in keyword_patterns:
            if pattern.search(review['text']):  # Use regex to search for whole words
                filtered_reviews.append(review)
                break  # Stop checking other keywords if one matches

    return filtered_reviews




# # -------------------------------FUNCTION TO GET OFFICIAL NAME/ADDRESS/----------------------------#
def get_apartment_details(place_id, GOOGLE_API_KEY):
    url = f"https://maps.googleapis.com/maps/api/place/details/json"

    # Define the parameters for the API request
    params = {
        'place_id': place_id,
        'fields': 'name,formatted_address,url,user_ratings_total',
        'key': GOOGLE_API_KEY

    }

    # Make the API request
    response = requests.get(url, params=params)
    data = response.json()


    # Check if successful
    if response.status_code == 200 and 'result' in data:
        result = data['result']
        return{
            'name': result.get('name', 'N/A'),
            'formatted_address': result.get('formatted_address', 'N/A'),
            'reviews_count': result.get('user_ratings_total', 0),
            'url': result.get('url', 'N/A')
        }
    else:
        return {
            'name': None,
            'formatted_address': None,
            'url': None,
            'reviews_count': 0

        }

# # -------------------------------MAIN FUNCTION TO CHAIN ALL GOOGLE PLACES API FUNCTIONS---------------------------#

def main(place_name, zip_code, GOOGLE_API_KEY):
    # Get place ID
    place_id = get_place_id(place_name, zip_code, GOOGLE_API_KEY)

    if place_id is None:
        return None, 0, [], [], None

    # Get apartment details (name, address, URL, reviews_count)
    apartment_details = get_apartment_details(place_id, GOOGLE_API_KEY)
    # Use reviews_count from apartment_details
    reviews_count = apartment_details.get('reviews_count', 0)


    ######### Capture the Google Place URL from apartment details
    google_place_url = apartment_details.get('url', 'N/A')


    # Get apartment reviews and overall google rating)
    overall_rating, reviews, review_dates = get_place_reviews_and_rating(place_id, GOOGLE_API_KEY)

    if not reviews: # Check if reviews are missing
        return overall_rating, reviews_count, [], [], apartment_details

    # Filter reviews based on keywords
    keywords = ["roaches", "pests", "mice", "bugs", "bug", "rats", "rat", "rodent", "rodents", "roach", "insect", "insects", "silverfish", "pest", "cockroach", "cockroaches", "spider", "spiders", "infested", "infestation", "ant", "ants", "nasty", "dirty", "disgusting", "spray", "trash", "borax", "crawling", "exterminator", "fleas", "trash", "mold", "centipede"]
    filtered_reviews = filter_reviews(reviews, keywords)

    #Filter corresponding review dates with filtered reviews
    filtered_dates = [review_dates[i] for i, review in enumerate(reviews) if review in filtered_reviews]






    if filtered_reviews:
        return overall_rating, reviews_count, filtered_reviews, filtered_dates, apartment_details
    else:
        return overall_rating, reviews_count, [], [], apartment_details






if __name__ == '__main__':
    app.run(debug=True)