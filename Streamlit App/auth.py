from supabase_client import supabase

def signup_user(email,password):
    response=supabase.auth.sign_up({
        "email":email,
        "password":password
    })
    return response

if __name__=="__main__":
    response=signup_user(
        "ashbeltheboss@gmail.com",
        "123456"
    )


def login_user(email,password):
    response=supabase.auth.sign_in_with_password({
        "email":email,
        "password":password
    })
    return response

