package com.junkyard.app;

import com.fasterxml.jackson.annotation.JsonProperty;

import java.util.Objects;

public class User {
    @JsonProperty("first_name")
    public String firstName;
    @JsonProperty("last_name")
    public String lastName;
    @JsonProperty("username")
    public String userName;

    @Override
    public int hashCode() {
        return Objects.hash(firstName, lastName);
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (!(o instanceof User other)) return false;
        return Objects.hash(this.firstName, this.lastName) == Objects.hash(other.firstName, other.lastName);
    }
}
